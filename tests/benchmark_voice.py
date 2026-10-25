"""Lightweight voice/tool latency smoke benchmarks (no mic required).

Run:
    python -m pytest tests/benchmark_voice.py -v
"""

from __future__ import annotations

import time

import pytest

from backend.tools.orchestrator import ToolOrchestrator
from backend.tools.registry import build_default_registry
from backend.voice.sentences import SentenceBuffer
from backend.voice.tts import LocalTTS


@pytest.mark.asyncio
async def test_tool_latency_under_two_seconds():
    orch = ToolOrchestrator(build_default_registry(), timeout_seconds=2.0)
    started = time.perf_counter()
    call = await orch.run_tool_round(
        '{"tool": "lookup_order", "args": {"order_id": "ORD-1085"}}'
    )
    elapsed = (time.perf_counter() - started) * 1000.0
    assert call is not None
    assert call["result"]["ok"] is True
    assert elapsed < 2000.0
    print(f"\nlookup_order latency: {elapsed:.1f}ms")


@pytest.mark.asyncio
async def test_tts_first_sentence_synth():
    tts = LocalTTS()
    started = time.perf_counter()
    wav, sr, synth_ms, backend = await tts.synthesize(
        "Your order ORD-1085 is currently in transit."
    )
    elapsed = (time.perf_counter() - started) * 1000.0
    assert isinstance(wav, (bytes, bytearray))
    assert len(wav) > 44  # WAV header at minimum
    assert sr > 0
    print(f"\nTTS backend={backend} synth_ms={synth_ms:.1f} wall_ms={elapsed:.1f}")


def test_sentence_streaming_splits_before_full_reply():
    buf = SentenceBuffer()
    first = buf.push("Tracking shows your package left the hub.")
    assert first == ["Tracking shows your package left the hub."]
    rest = buf.push(" It should arrive tomorrow.")
    assert rest == ["It should arrive tomorrow."]
