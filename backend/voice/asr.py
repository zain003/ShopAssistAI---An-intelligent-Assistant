"""Local speech-to-text via faster-whisper (CPU)."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from typing import Any, Optional, Tuple

import numpy as np

logger = logging.getLogger("backend.voice.asr")

_WHISPER_MODEL: Any = None
_WHISPER_LOCK = threading.Lock()
_WHISPER_LOAD_ERROR: Optional[str] = None


def _model_size() -> str:
    return os.getenv("ASR_MODEL_SIZE", "tiny.en")


def _get_whisper_model() -> Any:
    """Lazy-load a shared faster-whisper model (process-wide)."""
    global _WHISPER_MODEL, _WHISPER_LOAD_ERROR
    if _WHISPER_MODEL is not None:
        return _WHISPER_MODEL
    with _WHISPER_LOCK:
        if _WHISPER_MODEL is not None:
            return _WHISPER_MODEL
        try:
            from faster_whisper import WhisperModel

            size = _model_size()
            logger.info("Loading faster-whisper model '%s' on CPU...", size)
            _WHISPER_MODEL = WhisperModel(
                size,
                device="cpu",
                compute_type=os.getenv("ASR_COMPUTE_TYPE", "int8"),
            )
            logger.info("faster-whisper model ready.")
            return _WHISPER_MODEL
        except Exception as exc:
            _WHISPER_LOAD_ERROR = str(exc)
            logger.exception("Failed to load faster-whisper: %s", exc)
            raise RuntimeError(
                f"ASR unavailable: {exc}. Install faster-whisper and ensure the model can download."
            ) from exc


def pcm16_to_float32(pcm_bytes: bytes) -> np.ndarray:
    """Convert little-endian int16 PCM bytes to float32 mono samples in [-1, 1]."""
    if not pcm_bytes:
        return np.zeros(0, dtype=np.float32)
    n = len(pcm_bytes) - (len(pcm_bytes) % 2)
    audio = np.frombuffer(pcm_bytes[:n], dtype=np.int16).astype(np.float32)
    audio /= 32768.0
    return audio


def _transcribe_sync(pcm_bytes: bytes, sample_rate: int) -> Tuple[str, float]:
    started = time.perf_counter()
    model = _get_whisper_model()
    audio = pcm16_to_float32(pcm_bytes)
    if audio.size == 0:
        return "", (time.perf_counter() - started) * 1000.0

    # Resample to 16 kHz if needed (simple linear)
    target_sr = 16000
    if sample_rate != target_sr and sample_rate > 0:
        duration = audio.size / float(sample_rate)
        target_len = max(int(duration * target_sr), 1)
        x_old = np.linspace(0.0, 1.0, num=audio.size, endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=target_len, endpoint=False)
        audio = np.interp(x_new, x_old, audio).astype(np.float32)

    segments, _info = model.transcribe(
        audio,
        language="en",
        beam_size=1,
        vad_filter=True,
        without_timestamps=True,
    )
    parts = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
    text = " ".join(parts).strip()
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return text, elapsed_ms


class LocalASR:
    """Async wrapper around faster-whisper with thread-pool offload."""

    def __init__(self) -> None:
        self._executor_lock = asyncio.Lock()

    async def warmup(self) -> bool:
        try:
            await asyncio.to_thread(_get_whisper_model)
            return True
        except Exception as exc:
            logger.warning("ASR warmup failed: %s", exc)
            return False

    async def transcribe(
        self,
        pcm_bytes: bytes,
        sample_rate: int = 16000,
    ) -> Tuple[str, float]:
        """Transcribe PCM16 mono audio. Returns (transcript, asr_ms)."""
        async with self._executor_lock:
            return await asyncio.to_thread(_transcribe_sync, pcm_bytes, sample_rate)

    @property
    def load_error(self) -> Optional[str]:
        return _WHISPER_LOAD_ERROR
