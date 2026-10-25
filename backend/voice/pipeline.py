"""Per-connection voice session helpers (audio buffer + ASR/TTS engines)."""

from __future__ import annotations

import base64
import logging
from typing import List, Optional, Tuple

from backend.voice.asr import LocalASR
from backend.voice.tts import LocalTTS
from backend.voice.vad import SilenceDetector, concat_pcm

logger = logging.getLogger("backend.voice.pipeline")


class VoiceSessionBuffer:
    """Accumulate inbound PCM chunks for one utterance."""

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self.chunks: List[bytes] = []
        self.vad = SilenceDetector()
        self.speech_ended = False

    def reset(self) -> None:
        self.chunks.clear()
        self.vad.reset()
        self.speech_ended = False

    def add_chunk(self, pcm_bytes: bytes, sample_rate: Optional[int] = None) -> bool:
        if sample_rate:
            self.sample_rate = sample_rate
        if pcm_bytes:
            self.chunks.append(pcm_bytes)
            if self.vad.observe(pcm_bytes):
                self.speech_ended = True
                return True
        return False

    def pcm(self) -> bytes:
        return concat_pcm(self.chunks)


class VoicePipeline:
    """Shared ASR/TTS engines used by WebSocket handlers."""

    def __init__(
        self,
        asr: Optional[LocalASR] = None,
        tts: Optional[LocalTTS] = None,
    ) -> None:
        self.asr = asr or LocalASR()
        self.tts = tts or LocalTTS()

    async def warmup(self) -> None:
        await self.asr.warmup()
        await self.tts.warmup()

    async def transcribe_buffer(
        self,
        buffer: VoiceSessionBuffer,
    ) -> Tuple[str, float]:
        pcm = buffer.pcm()
        if not pcm:
            return "", 0.0
        return await self.asr.transcribe(pcm, sample_rate=buffer.sample_rate)

    @staticmethod
    def decode_audio_payload(payload: dict) -> Tuple[bytes, int]:
        """Decode base64 PCM from an audio_chunk payload."""
        b64 = payload.get("data") or payload.get("audio") or ""
        sample_rate = int(payload.get("sample_rate") or 16000)
        if not b64:
            return b"", sample_rate
        try:
            return base64.b64decode(b64), sample_rate
        except Exception:
            logger.warning("Failed to decode audio chunk base64")
            return b"", sample_rate

    @staticmethod
    def encode_wav_b64(wav_bytes: bytes) -> str:
        return base64.b64encode(wav_bytes).decode("ascii")
