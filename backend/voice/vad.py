"""Simple energy-based voice activity / end-of-speech detection."""

from __future__ import annotations

import struct
from typing import List


def pcm16_rms(pcm_bytes: bytes) -> float:
    """Compute RMS amplitude for little-endian int16 PCM."""
    if not pcm_bytes or len(pcm_bytes) < 2:
        return 0.0
    # Ensure even length
    n = len(pcm_bytes) - (len(pcm_bytes) % 2)
    if n < 2:
        return 0.0
    count = n // 2
    samples = struct.unpack(f"<{count}h", pcm_bytes[:n])
    if not samples:
        return 0.0
    acc = sum(float(s) * float(s) for s in samples)
    return (acc / len(samples)) ** 0.5


class SilenceDetector:
    """Detect end of speech after sustained low-energy frames."""

    def __init__(
        self,
        silence_rms_threshold: float = 350.0,
        silence_chunks_required: int = 8,
        min_speech_chunks: int = 3,
    ) -> None:
        self.silence_rms_threshold = silence_rms_threshold
        self.silence_chunks_required = silence_chunks_required
        self.min_speech_chunks = min_speech_chunks
        self._silence_streak = 0
        self._speech_chunks = 0
        self._heard_speech = False

    def reset(self) -> None:
        self._silence_streak = 0
        self._speech_chunks = 0
        self._heard_speech = False

    def observe(self, pcm_bytes: bytes) -> bool:
        """Feed a PCM chunk. Returns True when end-of-speech is detected."""
        rms = pcm16_rms(pcm_bytes)
        if rms >= self.silence_rms_threshold:
            self._heard_speech = True
            self._speech_chunks += 1
            self._silence_streak = 0
            return False

        if not self._heard_speech:
            return False

        self._silence_streak += 1
        if (
            self._speech_chunks >= self.min_speech_chunks
            and self._silence_streak >= self.silence_chunks_required
        ):
            return True
        return False


def concat_pcm(chunks: List[bytes]) -> bytes:
    return b"".join(chunks)
