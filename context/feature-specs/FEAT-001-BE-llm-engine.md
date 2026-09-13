# FEAT-001-BE — Local LLM Engine & CPU Streaming Adapter (P0)

**Layer**: Backend  
**Goal**: Provide an asynchronous streaming client for a local CPU-quantized LLM (Ollama / Qwen2.5-1.5B Q4_K_M) that emits token chunks and calculates Time-To-First-Token (TTFT) and throughput telemetry.

---

## Depends on / Context pack / Consumes
**Depends on**: `context/feature-specs/000-shared-contracts.md`  
**Context pack**:
```python
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, AsyncGenerator, Tuple

class StreamEndPayload(BaseModel):
    model_config = ConfigDict(frozen=True)
    turn_id: str
    total_tokens: int
    ttft_ms: float
    total_duration_ms: float
    tokens_per_second: float

class ErrorPayload(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str
    message: str
    recoverable: bool = True
```
**Consumes**: `StreamEndPayload`, `ErrorPayload` from `000-shared-contracts.md`.

---

## Provides / Exposes
```python
class LLMEngine:
    def __init__(self, host: str = "http://127.0.0.1:11434", model: str = "qwen2.5:1.5b"): ...
    async def is_ready(self) -> bool: ...
    async def warmup(self) -> bool: ...
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        turn_id: str,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> AsyncGenerator[Tuple[str, Optional[StreamEndPayload]], None]: ...
```

---

## Scope
- **Scope (In)**:
  - Local Ollama HTTP/streaming client using `httpx.AsyncClient`.
  - Asynchronous chunk parser extracting delta tokens from streaming JSON lines.
  - Telemetry computation: records `t_start`, calculates `ttft_ms` on first token chunk, and computes `tokens_per_second` upon completion.
  - Model warmup ping during application startup.
- **Scope (Out)**:
  - Prompt orchestration and session memory management (covered in `FEAT-002-BE`).
  - WebSocket routing and frame distribution (covered in `FEAT-003-BE`).

---

## Tech & Files to Touch
- `backend/core/config.py` — Host settings, model name (`OLLAMA_MODEL=qwen2.5:1.5b`), timeout defaults.
- `backend/core/llm.py` — `LLMEngine` implementation using `httpx`.
- `tests/test_llm_engine.py` — Unit tests with mocked httpx streaming responses.

---

## Tests to Write FIRST
1. `test_engine_is_ready_true_on_200`: Mock `GET /api/tags` returning 200 with model present -> returns `True`.
2. `test_engine_is_ready_false_on_connection_error`: Mock connection failure -> returns `False`.
3. `test_generate_stream_yields_tokens`: Mock streamed chunks `["Hello", " there", "!"]` -> yields 3 token tuples.
4. `test_generate_stream_emits_telemetry_at_end`: Verify final tuple contains `StreamEndPayload` with `ttft_ms > 0` and `total_tokens == 3`.
5. `test_generate_stream_raises_on_http_error`: Mock HTTP 500 error -> raises `LLMEngineError(code="INFERENCE_FAILED")`.

---

## Implementation Steps
1. Create `backend/core/config.py` with `OLLAMA_BASE_URL` (default `"http://localhost:11434"`) and `MODEL_NAME` (`"qwen2.5:1.5b"`).
2. Create custom exceptions `LLMEngineError` in `backend/core/llm.py`.
3. Implement `LLMEngine.__init__` with persistent `httpx.AsyncClient(timeout=60.0)`.
4. Implement `is_ready` hitting `/api/version` or `/api/tags`.
5. Implement `warmup` sending a 1-token test prompt (`"Hi"`).
6. Implement `generate_stream` using `client.stream("POST", "/api/chat", json=payload)`, parsing streaming lines, measuring timestamps, and yielding `(token, None)` followed by `("", StreamEndPayload)`.

---

## Acceptance Criteria
- [ ] `is_ready()` returns `True` if Ollama responds within 2.0 seconds.
- [ ] `generate_stream()` yields strings without buffering the entire response.
- [ ] Final yielded tuple has non-empty `StreamEndPayload` containing `turn_id`, `ttft_ms >= 0.0`, and `tokens_per_second > 0.0`.
- [ ] An unreachable Ollama host raises `LLMEngineError` with `code="SERVICE_UNAVAILABLE"`.
- [ ] Zero external cloud API endpoints are called.

---

## Definition of Done
- [ ] Unit tests pass 100% (`pytest tests/test_llm_engine.py`).
- [ ] Type check clean with zero errors under `mypy`.
- [ ] No TODO or placeholder comments left in `backend/core/llm.py`.

---

## Edge Cases to Handle
- First token delay: handle cases where CPU warmup causes TTFT > 3000ms on first run.
- Empty token chunks: filter out empty string chunks before yielding.
- Premature stream disconnect: clean up `httpx.Response` context cleanly without leaving dangling sockets.

---

## Pre-flight Check
Before starting, confirm `000-shared-contracts.md` exists and contains `StreamEndPayload`.

---

## What's Next
- `FEAT-001-VERIFY-llm-engine.md` — Verification pass for local LLM adapter.
- `FEAT-002-BE-prompt-orchestrator.md` — Conversation manager and prompt orchestrator.

---

## Ambiguity Resolution Protocol
If you encounter a case not covered by this spec:
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log it in `context/feature-specs/DEVIATIONS.md` as: `[FEAT-001-BE] — [what was ambiguous] — [assumption made]`.
4. Continue implementation; do not block unless it alters `000-shared-contracts.md`.
