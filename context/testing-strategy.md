# SQA Testing Strategy & Quality Standards

## Role & Philosophy

You are a Senior SQA Automation & Test Engineer. Your objective is 100% end-to-end quality confidence for every feature of the **E-Commerce Order Support Assistant (ShopAssist AI)** before it is marked complete. No code moves forward with failing tests. Every layer—Frontend (Fake DOM / UI), API routes & WebSockets, Backend dialogue logic, and in-memory session storage—must be rigorously verified against functional requirements, latency benchmarks, and adversarial edge cases.

---

## Multi-Layer Testing Architecture

```
+-------------------------------------------------------------------------+
|                    SHOPASSIST FULL-STACK SQA MATRIX                     |
+-------------------------------------------------------------------------+
|  1. FRONTEND LAYER    | Fake DOM (jsdom / Node test runner / Vitest)    |
|                       | Chat bubble rendering, streaming cursor,        |
|                       | citation badges, preview drawer, telemetry pills |
+-----------------------+-------------------------------------------------+
|  2. API LAYER         | FastAPI TestClient + async WebSocket testing    |
|                       | /ws/chat streaming protocol, JSON envelopes,    |
|                       | REST health endpoints, concurrency, errors     |
+-----------------------+-------------------------------------------------+
|  3. BACKEND & RAG     | Pytest unit tests (Python 3.11+)                |
|                       | Offline indexing, chunking, CPU embeddings,     |
|                       | vector retrieval, sliding window, prompt XML    |
+-----------------------+-------------------------------------------------+
|  4. BENCHMARK & EVAL  | Automated latency, RAG & adversarial evaluator  |
|                       | Retrieval latency (< 1.0s), TTFT (< 1.5s),      |
|                       | grounding accuracy, 100% Phase IV fallback      |
+-------------------------------------------------------------------------+
```

---

## Layer-by-Layer SQA Standards

### 1. Frontend Testing (Fake DOM & UI Interaction)
- **Environment**: Simulated DOM using `jsdom` or lightweight Node/Jest test runner.
- **Component Tests**:
  - Verify chat message list renders user and assistant message bubbles with correct styling classes.
  - Verify typing/streaming cursor indicator appears while streaming is active and disappears upon completion.
  - Verify citation badge row renders when `citations` are returned; clicking badge toggles expandable excerpt drawer.
  - Verify telemetry badge renders both `Retrieval: {retrieval_ms}ms` and `TTFT: {ttft_ms}ms`.
  - Verify "Reset Session" button clears chat history and sends a reset event.
- **Network Mocking**: Mock the WebSocket connection using an event-emitter mock to simulate incoming `token`, `citations`, and `stream_end` frames.

### 2. API Contract & WebSocket Testing
- **WebSocket Streaming (`/ws/chat`)**:
  - Test valid handshake and immediate `session_created` or `session_resumed` frame.
  - Test streaming reception of sequential `token` chunks ending with `stream_end`.
  - Verify latency telemetry payload in `stream_end` (TTFT, total time, retrieval time, citation list).
  - Test malformed JSON payloads: assert the server responds with an `error` frame with code `INVALID_PAYLOAD` and keeps connection alive.
  - Test unexpected disconnect during streaming: ensure no unhandled exceptions or thread leaks occur.
- **Concurrency**: Run 5 concurrent async WebSocket client connections simultaneously and assert no cross-talk or blocking between sessions.

### 3. Backend Logic, Indexing & RAG Retrieval Testing
- **Offline Indexing Pipeline**:
  - Verify ingestion of 50–100 markdown documents from `data/documents/`.
  - Verify chunking respects header tags and produces chunks between 300 and 500 characters.
  - Verify all embeddings have exactly 384 dimensions (`all-MiniLM-L6-v2`).
  - Verify SHA-256 fingerprinting: duplicate run performs 0 re-embeddings.
- **Vector Retrieval & Prompt Grounding**:
  - Verify query returns top-$k$ ($k \ge 3$) chunks ranked by cosine similarity.
  - Verify query LRU cache serves repeated questions in under 10 milliseconds.
  - Verify prompt token budget: `<retrieved_context>` is bounded strictly to 500 tokens.
- **Phase IV Failure Recovery**:
  - *No Relevant Matches*: Query with score < 0.45 triggers `is_fallback=True` without hallucinating facts.
  - *Retrieval Timeout*: Simulated delay > 1.0s triggers graceful fallback to general conversation without crashing.
  - *Context Overflow*: Sliding window truncates older history before dropping retrieved documents.

### 4. Latency Benchmarks & Production Readiness Evaluation
- **Latency Benchmarks**:
  - Vector Retrieval Latency: must be measured separately from generation time. Target: < 1,000ms on CPU (< 10ms for cached queries).
  - Time-To-First-Token (TTFT): measured in milliseconds. Target: < 1,500ms on local CPU.
  - Generation Throughput: tokens per second calculated over total response length. Target: > 10 tokens/sec on CPU.
- **Grounding Fidelity Evaluation**:
  - Evaluate standard domain queries (return policy, warranties, manuals) and assert responses contain accurate facts matching indexed docs.
- **Adversarial Evaluation Matrix**:
  - Test at least 5 adversarial prompts attempting jailbreaks, topic shifts, or tool requests.
  - Verify 100% of adversarial prompts are deflected back to e-commerce order support.

---

## Stop-the-Line Quality Gate

1. **Zero Failing Tests**: If any unit, API, or integration test fails, stop immediately and fix the defect before proceeding to the next feature spec.
2. **Deterministic Execution**: Tests must not rely on live internet connections or external paid APIs. LLM calls during unit and API integration tests must use deterministic mock streams or a local test fixture.
3. **Dedicated Test Reports**: Each feature must have a corresponding test report written to `feature-test-reports/FEAT-XXX-test-report.md` before being marked complete.

---

## Definition of Done (DoD) Checklist

Before any feature is approved:
- [ ] Multi-layer automated tests pass 100% (`pytest tests/`).
- [ ] Frontend fake DOM tests pass without errors.
- [ ] API WebSocket contracts match `000-shared-contracts.md`.
- [ ] Latency benchmarks (TTFT, tokens/sec) measured and documented.
- [ ] Out-of-domain queries verified to deflect gracefully.
- [ ] Test report generated and committed in `feature-test-reports/FEAT-XXX-test-report.md`.
- [ ] `context/progress-tracker.md` and `context/feature-specs/INDEX.md` updated.
