"""Local text-to-speech via Piper (with graceful pyttsx3 fallback)."""

from __future__ import annotations

import asyncio
import io
import logging
import os
import struct
import tempfile
import threading
import time
import wave
from typing import Any, Optional, Tuple

logger = logging.getLogger("backend.voice.tts")

_PIPER_VOICE: Any = None
_PIPER_LOCK = threading.Lock()
_TTS_BACKEND: Optional[str] = None  # "piper" | "pyttsx3" | "sine"


def _wav_bytes_from_pcm(pcm: bytes, sample_rate: int, sample_width: int = 2, channels: int = 1) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def _sine_placeholder(text: str, sample_rate: int = 22050) -> bytes:
    """Deterministic short tone so demos still produce audio if TTS deps missing."""
    import math

    duration = min(0.35 + 0.04 * len(text.split()), 2.5)
    n = int(sample_rate * duration)
    freq = 440.0
    pcm = bytearray()
    for i in range(n):
        # Soft envelope
        env = 1.0
        if i < sample_rate * 0.02:
            env = i / (sample_rate * 0.02)
        elif i > n - sample_rate * 0.05:
            env = max((n - i) / (sample_rate * 0.05), 0.0)
        sample = int(12000 * env * math.sin(2 * math.pi * freq * (i / sample_rate)))
        pcm += struct.pack("<h", max(-32767, min(32767, sample)))
    return _wav_bytes_from_pcm(bytes(pcm), sample_rate)


def _load_piper() -> Any:
    global _PIPER_VOICE, _TTS_BACKEND
    if _PIPER_VOICE is not None:
        return _PIPER_VOICE
    with _PIPER_LOCK:
        if _PIPER_VOICE is not None:
            return _PIPER_VOICE
        model_path = os.getenv("PIPER_MODEL_PATH", "").strip()
        if not model_path or not os.path.isfile(model_path):
            # Common default relative path for assignment setup
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            candidate = os.path.join(
                project_root, "models", "piper", "en_US-lessac-medium.onnx"
            )
            if os.path.isfile(candidate):
                model_path = candidate
            else:
                raise FileNotFoundError(
                    "PIPER_MODEL_PATH not set and default voice model not found"
                )
        from piper import PiperVoice  # type: ignore

        logger.info("Loading Piper voice from %s", model_path)
        _PIPER_VOICE = PiperVoice.load(model_path)
        _TTS_BACKEND = "piper"
        return _PIPER_VOICE


def _synth_piper(text: str) -> Tuple[bytes, int]:
    voice = _load_piper()
    sample_rate = int(getattr(getattr(voice, "config", None), "sample_rate", 22050))
    audio_buf = io.BytesIO()
    with wave.open(audio_buf, "wb") as wf:
        voice.synthesize(text, wf)
    return audio_buf.getvalue(), sample_rate


def _synth_pyttsx3(text: str) -> Tuple[bytes, int]:
    import pyttsx3

    engine = pyttsx3.init()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    try:
        engine.save_to_file(text, path)
        engine.runAndWait()
        with open(path, "rb") as fh:
            data = fh.read()
        # Read sample rate from WAV header if possible
        sample_rate = 22050
        try:
            with wave.open(io.BytesIO(data), "rb") as wf:
                sample_rate = wf.getframerate()
        except Exception:
            pass
        return data, sample_rate
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _synthesize_sync(text: str) -> Tuple[bytes, int, float, str]:
    started = time.perf_counter()
    clean = (text or "").strip()
    if not clean:
        return b"", 22050, 0.0, "none"

    backend = os.getenv("TTS_BACKEND", "auto").lower()
    errors = []

    if backend in ("auto", "piper"):
        try:
            wav, sr = _synth_piper(clean)
            elapsed = (time.perf_counter() - started) * 1000.0
            return wav, sr, elapsed, "piper"
        except Exception as exc:
            errors.append(f"piper: {exc}")
            if backend == "piper":
                raise

    if backend in ("auto", "pyttsx3"):
        try:
            wav, sr = _synth_pyttsx3(clean)
            elapsed = (time.perf_counter() - started) * 1000.0
            return wav, sr, elapsed, "pyttsx3"
        except Exception as exc:
            errors.append(f"pyttsx3: {exc}")
            if backend == "pyttsx3":
                raise

    # Last resort placeholder so the pipeline still streams audio chunks
    logger.warning("TTS backends unavailable (%s); using tone placeholder", "; ".join(errors))
    wav = _sine_placeholder(clean)
    elapsed = (time.perf_counter() - started) * 1000.0
    return wav, 22050, elapsed, "sine"


class LocalTTS:
    """Async sentence synthesizer with thread-pool offload."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def warmup(self) -> bool:
        try:
            await self.synthesize("Ready.")
            return True
        except Exception as exc:
            logger.warning("TTS warmup failed: %s", exc)
            return False

    async def synthesize(self, text: str) -> Tuple[bytes, int, float, str]:
        """Synthesize text to WAV bytes. Returns (wav, sample_rate, ms, backend)."""
        async with self._lock:
            return await asyncio.to_thread(_synthesize_sync, text)
