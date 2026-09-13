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
|                       | connection status badge, session reset action   |
+-----------------------+-------------------------------------------------+
|  2. API LAYER         | FastAPI TestClient + async WebSocket testing    |
|                       | /ws/chat streaming protocol, JSON envelopes,    |
|                       | REST health endpoints, concurrency, errors     |
+-----------------------+-------------------------------------------------+
|  3. BACKEND LAYER     | Pytest unit tests (Python 3.11+)                |
|                       | Sliding window memory, prompt XML assembly,     |
|                       | domain policy enforcement, entity tracking      |
+-----------------------+-------------------------------------------------+
|  4. BENCHMARK & EVAL  | Automated latency & adversarial test runner     |
|                       | Time-To-First-Token (TTFT), tokens/second,      |
|                       | 100% deflection of out-of-domain queries        |
+-------------------------------------------------------------------------+
```

---

## Layer-by-Layer SQA Standards

### 1. Frontend Testing (Fake DOM & UI Interaction)
- **Environment**: Simulated DOM using `jsdom` or lightweight Node/Jest test runner.
- **Component Tests**:
  - Verify chat message list renders user and assistant message bubbles with correct styling classes.
  - Verify typing/streaming cursor indicator appears while streaming is active and disappears upon completion.
  - Verify "Reset Session" button clears chat history and sends a reset event.
  - Verify disconnected state displays an appropriate alert badge.
- **Network Mocking**: Mock the WebSocket connection using an event-emitter mock to simulate incoming `token` and `stream_end` frames.

### 2. API Contract & WebSocket Testing
- **WebSocket Streaming (`/ws/chat`)**:
  - Test valid handshake and immediate `session_created` or `session_resumed` frame.
  - Test streaming reception of sequential `token` chunks ending with `stream_end`.
  - Verify latency telemetry payload in `stream_end` (TTFT, total time, token count).
  - Test malformed JSON payloads: assert the server responds with an `error` frame with code `INVALID_PAYLOAD` and keeps connection alive.
  - Test unexpected disconnect during streaming: ensure no unhandled exceptions or thread leaks occur.
- **Concurrency**: Run 5 concurrent async WebSocket client connections simultaneously and assert no cross-talk or blocking between sessions.

### 3. Backend Logic & Prompt Orchestration Testing
- **Session Memory Management**:
  - Test sliding window truncation: populate session with 15 turns and verify it trims to the configured maximum (e.g. 6 turns / 12 messages) without dropping the persistent system prompt.
  - Test entity tracking: ensure `order_id` (e.g. `ORD-1002`) remains bound to the session across turns.
- **Prompt Construction**:
  - Verify system prompt includes `<store_catalog>`, `<order_records>`, `<store_policies>`, and `<conversation_rules>`.
  - Verify no empty or duplicate sections.
- **Deflection & Policy Rules**:
  - Test out-of-domain queries (coding, math, politics): verify the prompt orchestrator produces or guides the response to the standard deflection response.

### 4. Latency Benchmarks & Production Readiness Evaluation
- **Latency Benchmarks**:
  - Time-To-First-Token (TTFT): must be measured and reported in milliseconds. Target: < 1,500ms on local CPU.
  - Generation Throughput: tokens per second calculated over total response length. Target: > 10 tokens/sec on CPU.
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
