# Architecture Context

## Stack

| Layer                | Technology                         | Role                                                            |
| -------------------- | ---------------------------------- | --------------------------------------------------------------- |
| **Backend API**      | FastAPI + Uvicorn (Python 3.11+)   | Asynchronous REST & WebSocket server (`/ws/chat`, `/api/health`)|
| **Protocol**         | WebSocket (RFC 6455) + JSON        | Full-duplex, low-latency streaming of token chunks & telemetry  |
| **LLM Engine**       | Local CPU Inference (Ollama client)| Quantized 0.5B–3B model (Qwen2.5-1.5B Q4_K_M / Phi-3-mini)     |
| **Retrieval Module** | Sentence-Transformers + CPU Store  | Local `all-MiniLM-L6-v2` embeddings, cosine vector store, cache |
| **Dialogue Manager** | Pure Python Orchestrator           | In-memory session store, sliding-window memory, RAG prompt injection |
| **Knowledge Base**   | 50–100 Local Domain Documents      | Markdown files in `data/documents/` indexed into vector store   |
| **Frontend UI**      | Vanilla Modern Web (HTML5/CSS3/JS) | Real-time chat interface, streaming renderer, citation cards    |
| **Testing**          | Pytest + pytest-asyncio + Fake DOM | Multi-layer test suite covering API, RAG, logic, UI, and eval   |

---

## Architecture Flow

```
Web UI <--WebSocket--> FastAPI Backend <--> Conversation Manager <--> Local LLM Engine
                                                |
                                                +--> Retrieval Module (Embedding + Vector Store)
                                                            |
                                                    Document Collection (50-100 Docs)
```

---

## System Boundaries

- `backend/core/llm.py` — Encapsulates local LLM engine communication (Ollama). Exposes an async streaming generator `generate_stream(prompt, system_prompt)` yielding token chunks with latency telemetry (TTFT, tokens/sec).
- `backend/rag/indexer.py` — Offline, re-runnable indexing pipeline loading Markdown documents from `data/documents/`, performing header-aware chunking, generating 384d CPU embeddings, and maintaining SHA-256 incremental hash cache.
- `backend/rag/retriever.py` — Real-time asynchronous query retriever. Generates query embeddings in thread pool executor, queries CPU vector store for top-$k$ ($k \ge 3$) chunks, caches results in a 128-item LRU cache, and enforces 1.0s timeout.
- `backend/rag/vector_store.py` — Local CPU vector storage layer with disk serialization and cosine similarity computation.
- `backend/conversation/manager.py` — Manages multi-turn conversation sessions, in-memory dialogue histories, session resets, entity memory (`order_id`), and hooks into the vector retriever.
- `backend/conversation/orchestrator.py` — Constructs structured system prompts embedding domain persona, deflection rules, and dynamic `<retrieved_context>` blocks within a strict 500-token budget.
- `backend/conversation/memory.py` — Sliding-window token management and turn pruning to fit local CPU context limits (e.g. 2,048 tokens).
- `backend/api/websocket.py` — Manages WebSocket lifecycle, concurrent connections, JSON envelope validation, streaming token dispatch, and citation telemetry emission.
- `backend/api/routes.py` — REST endpoints for health checks, model metadata, and latency benchmarks.
- `frontend/` — Client web interface containing chat message stream rendering, citation pill badges with expandable excerpt drawers, and latency telemetry pills.
- `tests/` — Automated test suites adhering to `testing-strategy.md` across Frontend fake DOM, WebSocket contracts, vector retrieval, and benchmarks.

---

## Storage Model

- **In-Memory Session Store**:
  - Thread-safe dictionary/cache mapping `session_id` (UUID4) to `SessionState`.
  - Holds turn history (`role: "user" | "assistant"`, `content`, `timestamp`), extracted entities (`order_id`, `product_id`), and cumulative token estimates.
  - Automatically evicts stale sessions after inactivity timeout (e.g., 30 minutes).
- **Persistent Vector Store (`data/vector_store/`)**:
  - Persisted embeddings matrix, chunk texts, and document metadata on local disk.
  - `index_manifest.json`: Fingerprints source documents with SHA-256 hashes to skip redundant indexing.
- **Document Collection (`data/documents/`)**:
  - 50–100 clean Markdown files organized into domains (policies, shipping, products, warranties, troubleshooting).
- **Static Domain Datastores (Fallback Context)**:
  - `MOCK_ORDERS`: Fixed dictionary of mock customer orders (`ORD-1001` through `ORD-1005`) for order tracking.

---

## Auth and Session Model

- **Session Handshake**: The client provides an optional `session_id` upon WebSocket connection. If omitted or expired, the backend generates a new cryptographically secure UUID4 and emits a `session_created` event.
- **Session Isolation**: Each user session has its own independent dialogue memory. Concurrent WebSocket connections run asynchronously in separate asyncio Tasks and cannot leak or cross-contaminate state.

---

## Invariants

1. **Zero External Inference**: The system strictly forbids cloud LLM APIs (OpenAI, Anthropic, Cohere, etc.). All inference runs locally on CPU via quantized weights.
2. **Zero External Tools / Local RAG Only**: Retrieval is conducted purely against the local 50–100 document collection using local CPU embeddings. External web search, cloud APIs, and live agent tool executions remain strictly forbidden.
3. **Non-Blocking Asynchronous Concurrency**: All I/O, WebSocket reads/writes, streaming iterations, and CPU embedding/vector lookups must be asynchronous (`async`/`await` / thread pool executor), ensuring retrieval or inference for one user never freezes connections for concurrent sessions.
4. **Resilient Connection Lifecycle & Phase IV Fallbacks**: Malformed JSON payloads, retrieval timeouts, or low-similarity queries must emit structured messages and fallback cleanly without terminating the WebSocket connection.
5. **Bounded Memory & RAG Token Budget**: Context history and retrieved knowledge are strictly pruned using sliding-window and token budget algorithms, guaranteeing total prompt tokens stay within CPU budget (max 2,048 tokens; `<retrieved_context>` max 500 tokens).
