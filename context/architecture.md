# Architecture Context

## Stack

| Layer                | Technology                         | Role                                                            |
| -------------------- | ---------------------------------- | --------------------------------------------------------------- |
| **Backend API**      | FastAPI + Uvicorn (Python 3.11+)   | Asynchronous REST & WebSocket server (`/ws/chat`, `/api/health`)|
| **Protocol**         | WebSocket (RFC 6455) + JSON        | Full-duplex, low-latency streaming of token chunks              |
| **LLM Engine**       | Local CPU Inference (Ollama client)| Quantized 0.5B–3B model (Qwen2.5-1.5B Q4_K_M / Phi-3-mini)     |
| **Dialogue Manager** | Pure Python Orchestrator           | In-memory session store, sliding-window memory, prompt builder  |
| **Knowledge Base**   | In-Prompt Static Data Schemas      | Catalog items, mock orders, and policy rules embedded in prompt |
| **Frontend UI**      | Vanilla Modern Web (HTML5/CSS3/JS) | Real-time chat interface with streaming token rendering         |
| **Testing**          | Pytest + pytest-asyncio + Fake DOM | Multi-layer test suite covering API, logic, and UI              |

---

## System Boundaries

- `backend/core/llm.py` — Encapsulates local LLM engine communication (Ollama / llama-cpp). Exposes an async streaming generator `generate_stream(prompt, system_prompt)` yielding token chunks with latency telemetry (TTFT, tokens/sec).
- `backend/conversation/manager.py` — Manages multi-turn conversation sessions, in-memory dialogue histories, session resets, and entity memory (`order_id`, `customer_name`).
- `backend/conversation/orchestrator.py` — Constructs structured system prompts embedding domain persona, catalog specs, mock orders, and strict boundary rules without tools or RAG.
- `backend/conversation/memory.py` — Sliding-window token management and turn pruning to fit local CPU context limits (e.g. 2048/4096 tokens).
- `backend/api/websocket.py` — Manages WebSocket lifecycle, concurrent connections, JSON envelope validation, and streaming token dispatch.
- `backend/api/routes.py` — REST endpoints for health checks, model metadata, and latency benchmarks.
- `frontend/` — Client web interface containing chat message stream rendering, connection indicator, auto-scroll, and session reset controls.
- `tests/` — Automated test suites adhering to `testing-strategy.md` across Frontend fake DOM, WebSocket contracts, and memory pruning.

---

## Storage Model

- **In-Memory Session Store**:
  - Thread-safe dictionary/cache mapping `session_id` (UUID4) to `SessionState`.
  - Holds turn history (`role: "user" | "assistant"`, `content`, `timestamp`), extracted entities (`order_id`, `product_id`), and cumulative token estimates.
  - Automatically evicts stale sessions after inactivity timeout (e.g., 30 minutes).
- **Static Domain Datastores (Embedded in Prompt Context)**:
  - `MOCK_ORDERS`: Fixed dictionary of mock customer orders (`ORD-1001` through `ORD-1005`) with shipment status, tracking number, items, and delivery dates.
  - `CATALOG_PRODUCTS`: Structured product list with SKU, name, price, specs, warranty, and stock count.
  - `STORE_POLICIES`: Concise return and shipping policy terms injected into the system prompt.

---

## Auth and Session Model

- **Session Handshake**: The client provides an optional `session_id` upon WebSocket connection. If omitted or expired, the backend generates a new cryptographically secure UUID4 and emits a `session_created` event.
- **Session Isolation**: Each user session has its own independent dialogue memory. Concurrent WebSocket connections run asynchronously in separate asyncio Tasks and cannot leak or cross-contaminate state.

---

## Invariants

1. **Zero External Inference**: The system strictly forbids cloud LLM APIs (OpenAI, Anthropic, Cohere, etc.). All inference runs locally on CPU via quantized weights.
2. **Strictly No RAG or Tool Execution**: All knowledge is embedded directly into structured system prompts; the model does not call external functions, search engines, or database drivers at runtime.
3. **Non-Blocking Asynchronous Concurrency**: All I/O, WebSocket reads/writes, and streaming iterations must be asynchronous (`async`/`await`), ensuring slow inference for one user never freezes connections for other concurrent sessions.
4. **Resilient Connection Lifecycle**: Malformed JSON payloads or model inference timeouts must emit structured error messages (`{"type": "error", "message": "..."}`) and keep the WebSocket connection open rather than terminating ungracefully.
5. **Bounded Memory Footprint**: Context history per session is strictly pruned using a sliding window algorithm to guarantee total prompt tokens stay within CPU budget (max 2048 tokens).
