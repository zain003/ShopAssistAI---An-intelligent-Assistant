# FEAT-003-BE — FastAPI WebSocket Streaming API (P0)

**Layer**: Backend  
**Goal**: Expose an asynchronous FastAPI WebSocket endpoint `/ws/chat` that accepts user messages in JSON envelopes, streams LLM tokens word-by-word back to the client, handles session resets, and catches exceptions without dropping connections.

---

## Depends on / Context pack / Consumes
**Depends on**: `context/feature-specs/000-shared-contracts.md`, `FEAT-001-BE-llm-engine.md`, `FEAT-002-BE-prompt-orchestrator.md`  
**Context pack**:
```python
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional

class InboundEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: str  # "user_message" | "reset_session" | "ping"
    session_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class OutboundEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: str  # "session_created" | "stream_start" | "token" | "stream_end" | "error" | "pong"
    session_id: str
    payload: Dict[str, Any]
```
**Consumes**:
- `LLMEngine.generate_stream(messages, turn_id)` from `FEAT-001-BE`
- `ConversationManager.get_or_create_session(session_id)` from `FEAT-002-BE`
- `ConversationManager.add_user_message(session_id, content)` from `FEAT-002-BE`
- `ConversationManager.add_assistant_message(session_id, content)` from `FEAT-002-BE`
- `ConversationManager.build_chat_payload(session_id)` from `FEAT-002-BE`

---

## Provides / Exposes
```python
from fastapi import FastAPI, WebSocket

app: FastAPI
# REST Routes:
# GET  /api/health -> {"status": "ok", "model": str, "ready": bool}
# WebSocket Endpoint:
# /ws/chat (supports bidirectional JSON protocol)
async def websocket_chat_endpoint(websocket: WebSocket) -> None: ...
```

---

## Scope
- **Scope (In)**:
  - FastAPI application instantiation with CORS middleware enabled for local web client.
  - WebSocket `/ws/chat` connection lifecycle: handshake, session initialization, ping/pong heartbeats.
  - JSON message envelope deserialization and Pydantic validation.
  - Real-time token dispatch loop consuming `LLMEngine.generate_stream`.
  - Error isolation: malformed payloads emit `error` frame with code `INVALID_PAYLOAD` and keep socket open.
- **Scope (Out)**:
  - Frontend DOM rendering (handled in `FEAT-004-FE`).
  - Benchmarking runner scripts (handled in `FEAT-005-INT`).

---

## Tech & Files to Touch
- `backend/api/main.py` — FastAPI app creation and lifecycle startup warmup.
- `backend/api/routes.py` — REST `/api/health` endpoint.
- `backend/api/websocket.py` — WebSocket connection handler and streaming loop.
- `tests/test_websocket.py` — Integration tests using `fastapi.testclient.TestClient`.

---

## Tests to Write FIRST
1. `test_health_endpoint_returns_ok`: `GET /api/health` -> returns HTTP 200 with `status="ok"`.
2. `test_ws_connection_emits_session_created`: Connect WebSocket -> receives `session_created` frame with valid UUID.
3. `test_ws_user_message_streams_tokens_and_end`: Send `user_message` -> receives `stream_start`, multiple `token` frames, and `stream_end`.
4. `test_ws_malformed_json_emits_error_frame`: Send invalid JSON string `"{bad"` -> receives `error` frame with code `INVALID_PAYLOAD` without socket closing.
5. `test_ws_reset_session_emits_session_reset`: Send `reset_session` -> receives `session_reset` frame and clears conversation state.

---

## Implementation Steps
1. Create `backend/api/main.py` with FastAPI app, CORS middleware, and lifespan event initializing `LLMEngine` and `ConversationManager`.
2. Create `backend/api/routes.py` with `GET /api/health`.
3. Implement `backend/api/websocket.py` with `websocket_chat_endpoint`:
   - Accept connection and check query parameters or initial payload for `session_id`.
   - Send `session_created` frame.
   - Enter `while True:` loop reading JSON messages.
   - Handle `ping`, `reset_session`, and `user_message`.
   - On `user_message`, call `add_user_message`, build chat payload, send `stream_start`, iterate `generate_stream` yielding `token` frames, save full assistant response, and send `stream_end`.

---

## Acceptance Criteria
- [ ] `/ws/chat` accepts connections and immediately returns a `session_created` frame.
- [ ] Sending a `user_message` results in sequential `token` frames followed by a `stream_end` frame.
- [ ] Sending invalid JSON returns an `error` frame with `recoverable=True` and does not terminate the connection.
- [ ] Sending `reset_session` zeroes history and returns `session_reset`.
- [ ] Concurrency test: 5 simultaneous connections stream responses without blocking one another.

---

## Definition of Done
- [ ] All WebSocket integration tests pass (`pytest tests/test_websocket.py`).
- [ ] Fast startup warmup completes with zero exceptions.
- [ ] Type annotations pass `mypy`.

---

## Edge Cases to Handle
- Client disconnects mid-stream: catch `WebSocketDisconnect`, cancel LLM generation task, and clean up resources without crashing server.
- Empty text message: reject text with length 0, return `error` with code `EMPTY_MESSAGE`.
- LLM generation failure: catch exception, emit `error` frame with `code="INFERENCE_FAILED"`.

---

## Pre-flight Check
Confirm `FEAT-001-VERIFY` and `FEAT-002-VERIFY` have passed.

---

## What's Next
- `FEAT-003-VERIFY-websocket-api.md` — Verification pass.
- `FEAT-004-FE-chat-interface.md` — Web-based chat interface.

---

## Ambiguity Resolution Protocol
If you encounter a case not covered by this spec:
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log it in `context/feature-specs/DEVIATIONS.md` as: `[FEAT-003-BE] — [what was ambiguous] — [assumption made]`.
4. Continue implementation; do not block unless it alters `000-shared-contracts.md`.
