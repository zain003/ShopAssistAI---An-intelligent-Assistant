"""Incremental sentence splitter for streaming TTS."""

from __future__ import annotations

import re
from typing import List, Tuple

_SENTENCE_END = re.compile(r"([.!?])(\s+|$)")


class SentenceBuffer:
    """Accumulate streaming tokens and emit complete sentences."""

    def __init__(self) -> None:
        self._buf = ""

    def reset(self) -> None:
        self._buf = ""

    def push(self, token: str) -> List[str]:
        """Append token; return any newly completed sentences."""
        if not token:
            return []
        self._buf += token
        return self._drain(final=False)

    def flush(self) -> List[str]:
        """Emit any remaining buffered text as a final sentence."""
        return self._drain(final=True)

    def _drain(self, final: bool) -> List[str]:
        sentences: List[str] = []
        while True:
            match = _SENTENCE_END.search(self._buf)
            if not match:
                break
            end = match.end()
            # Keep trailing whitespace attached only up to the punctuation
            cut = match.start(1) + 1
            sentence = self._buf[:cut].strip()
            self._buf = self._buf[end:]
            if sentence:
                sentences.append(sentence)

        if final:
            leftover = self._buf.strip()
            self._buf = ""
            if leftover:
                sentences.append(leftover)
        return sentences


def split_sentences(text: str) -> List[str]:
    """Split a full string into sentences (utility for tests)."""
    buf = SentenceBuffer()
    out = buf.push(text)
    out.extend(buf.flush())
    return out
