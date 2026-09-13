# Progress Tracker

## Current Phase

- **Phase VI (SQA Tests, Latency Benchmarks & Adversarial Evaluation)**: Completed. `FEAT-005-INT` and `FEAT-005-VERIFY` 100% verified (47/47 backend tests passed, 9/9 frontend DOM tests passed, 56/56 total automated tests, 100% adversarial deflection, and full SQA report filed).
- **Next Phase**: Final Project Packaging, Documentation & Submission.

---

## Current Goal

- All 6 core implementation phases (`FEAT-001` through `FEAT-005`) are completed, benchmarked, and verified with zero defects.

---

## Milestones & Status

| Phase | Milestone Name                                | Status        | Notes / Artifacts                                |
| :---: | :-------------------------------------------- | :-----------: | :----------------------------------------------- |
| **I** | Business Case & Flow Design                   | **Completed** | `context/project-overview.md`                    |
| **-** | Context & Feature Specs Definition            | **Completed** | `context/` & `context/feature-specs/`            |
| **II**| Local LLM Setup & CPU Engine (`FEAT-001`)     | **Completed** | `FEAT-001-BE` + `FEAT-001-VERIFY`: 13/13 tests passed, SQA approved |
| **III**| Conversation Manager & Memory (`FEAT-002`)   | **Completed** | `FEAT-002-BE` + `FEAT-002-VERIFY`: 13/13 tests passed, SQA approved |
| **IV**| FastAPI WebSocket Streaming API (`FEAT-003`)  | **Completed** | `FEAT-003-BE` + `FEAT-003-VERIFY`: 13/13 tests passed, SQA approved |
| **V** | Web Chat Interface (`FEAT-004`)               | **Completed** | `FEAT-004-FE` + `FEAT-004-VERIFY`: 9/9 tests passed, SQA approved |
| **VI**| SQA Tests, Benchmarks & Reports (`FEAT-005`)  | **Completed** | `FEAT-005-INT` + `FEAT-005-VERIFY`: 8/8 unit tests, 56 total tests, 100% deflection, SQA report approved |

---

## Architecture Decisions (ADR)

1. **AD-001 (Domain Selection)**: Chose **E-Commerce Order Support Assistant** ("ShopAssist AI"). Provides a rich, highly structured domain with multi-turn flows (order tracking, catalog recommendations, return policy inquiries, and mid-conversation topic shifts).
2. **AD-002 (Local Model)**: Selected **Qwen2.5-1.5B-Instruct (or 3B) Q4_K_M** running via local Ollama instance. Fits comfortably in CPU memory (under 1.5 GB RAM footprint) and delivers 15–25 tokens/second with TTFT < 1.0s on standard multicore CPUs.
3. **AD-003 (Strict Zero-Tool / Zero-RAG Architecture)**: Per assignment constraints, all product catalog specs, mock orders, and policy rules are embedded directly into structured XML system prompts. Intelligence is derived purely from prompt design and memory management.
4. **AD-004 (WebSocket Streaming Protocol)**: Designed an asynchronous JSON envelope protocol over `/ws/chat` (`stream_start`, `token`, `stream_end`, `error`) ensuring true word-by-word token streaming without HTTP polling overhead.
5. **AD-005 (Sliding-Window Memory Budget)**: Bounded memory to the last 6 conversation turns (12 messages) plus a static system prompt, maintaining total prompt context strictly under 2,048 tokens to preserve CPU inference speed.

---

## Open Questions / Risks

- *Risk*: First-turn cold start latency when Ollama loads the model into CPU RAM.
  - *Mitigation*: Implement a server startup warmup routine that sends a dummy 1-token prompt to preload weights before accepting client WebSocket connections.

---

## Session Notes

- All 7 context files in `context/` synchronized with the E-Commerce domain requirements.
- Feature specification suite (`000-shared-contracts.md`, `INDEX.md`, `DEVIATIONS.md`, `FEAT-001` through `FEAT-005`) generated in `context/feature-specs/`.
- `FEAT-001-BE` (Local LLM Engine & CPU Streaming Adapter) implemented in `backend/core/llm.py`.
- `FEAT-001-VERIFY` executed and 100% completed:
  - 13/13 automated unit tests passing in `tests/test_llm_engine.py` (readiness probing, model filtering, chunk streaming, TTFT/duration/throughput telemetry, timeouts, and error handling).
  - Strict type checking clean via `mypy` across all core and test files.
  - Standards compliance established via `pytest.ini` and `requirements.txt`.
  - Comprehensive SQA verification report generated in `feature-test-reports/FEAT-001-test-report.md`.
  - Checklist in `context/feature-specs/FEAT-001-VERIFY-llm-engine.md` fully signed off.
- `FEAT-002-BE` (Conversation Manager & Prompt Orchestrator) implemented and passed:
  - Created `backend/conversation/data.py` embedding 6 catalog products, 5 mock customer orders, and store return/shipping policies.
  - Created `backend/conversation/memory.py` implementing sliding-window history pruning (bounded to 12 messages / 6 turns).
  - Created `backend/conversation/orchestrator.py` generating structured XML prompts (`<store_persona>`, `<catalog_products>`, `<mock_orders>`, `<store_policies>`, `<deflection_rules>`, and `<active_session_order>`).
  - Created `backend/conversation/manager.py` implementing thread-safe `ConversationManager` with automatic TTL eviction, regex entity extraction (`ORD-XXXX` and natural `order XXXX`), and chat payload assembly.
  - Built comprehensive unit test suite in `tests/test_conversation.py`: 13/13 unit tests passing (`100%`).
  - Full project test suite running clean at 26/26 passing tests with zero static typing errors under `mypy`.
- `FEAT-002-VERIFY` executed and 100% completed:
  - 13/13 automated unit tests verified in `tests/test_conversation.py`.
  - All 5 Acceptance Criteria (AC-1 through AC-5) verified and signed off.
  - SQA verification test report generated and committed in `feature-test-reports/FEAT-002-test-report.md`.
  - Definition of Done requirements fulfilled with zero failing tests and strict type checking clean.
- `FEAT-003-BE` (FastAPI WebSocket Streaming API) implemented and verified:
  - Created `backend/api/routes.py` with `GET /api/health` returning status, model name, and engine readiness probe.
  - Created `backend/api/websocket.py` with asynchronous `/ws/chat` endpoint supporting session auto-generation, bidirectional JSON envelope protocol, word-by-word LLM token streaming, heartbeat `ping`/`pong`, session reset, and resilient error recovery without socket termination.
  - Created `backend/api/main.py` application factory with CORS middleware, lifespan startup model warmup, and shutdown cleanup.
  - Created comprehensive integration test suite in `tests/test_websocket.py`: 13/13 integration tests passing (100%).
  - Full project test suite running clean at 39/39 passing tests with zero static typing errors under `mypy` across 18 source files.
- `FEAT-003-VERIFY` executed and 100% completed:
  - All 5 Acceptance Criteria (AC-1 through AC-5) verified and signed off.
  - SQA verification test report generated and committed in `feature-test-reports/FEAT-003-test-report.md`.
  - Definition of Done requirements fulfilled with zero failing tests, clean server launch, and strict type checking clean.
  - `FEAT-004-FE` (Web-Based Chat Interface & Real-Time Stream Renderer) implemented and verified:
  - Created `frontend/index.html` with semantic structure, header branding, live status badge, welcome card, quick action chips, and auto-expanding input area.
  - Created `frontend/style.css` strictly utilizing design tokens from `context/ui-context.md` (dark slate theme, glowing status indicators, blinking streaming cursor, glassmorphic badges).
  - Created `frontend/app.js` managing WebSocket connection lifecycle, exponential backoff reconnects, 30s heartbeats, token-by-token message accumulation, session resets, and TTFT/latency telemetry badge rendering.
  - Mounted `frontend/` static directory in `backend/api/main.py` enabling unified local serving via FastAPI at `http://localhost:8000/`.
  - Built comprehensive simulated DOM test suite in `tests/test_frontend.js`: 9/9 tests passing (100%).
  - Full project regression suite running clean at 39/39 passing tests with zero static typing errors under `mypy` across 18 source files.
- `FEAT-004-VERIFY` executed and 100% completed:
  - All 5 Acceptance Criteria (AC-1 through AC-5) verified and signed off.
  - SQA verification test report generated and committed in `feature-test-reports/FEAT-004-test-report.md`.
  - Checklists in `context/feature-specs/FEAT-004-VERIFY-chat-interface.md` fully signed off.
- `FEAT-005-INT` (Latency Benchmarks & Adversarial Evaluation Suite) implemented and verified:
  - Added `BenchmarkResult` and `AdversarialEvalResult` shared contracts in `backend/contracts.py`.
  - Reinforced system prompt `<deflection_rules>` and `DEFLECTION_DIRECTIVE` in `backend/conversation/orchestrator.py` & `data.py` with explicit negative constraints and few-shot deflection examples, achieving 100% deflection with 0 code or math leakage.
  - Created `tests/benchmark_latency.py` with `BenchmarkRunner` measuring TTFT, tokens/sec, total duration, and token count across 5 standard customer queries with run #0 warmup discarded.
  - Created `tests/eval_adversarial.py` with `AdversarialEvaluator` testing 5 hostile categories (`coding`, `math`, `politics`, `jailbreak`, `medical`) and regex deflection verification.
  - Created `tests/evaluation_suite.py` with `EvaluationSuite` orchestrating both harnesses and generating standardized markdown SQA test reports.
  - Built unit test suite in `tests/test_eval_and_benchmarks.py`: 8/8 unit tests passing (`100%`).
  - Executed live benchmarks on CPU: Mean TTFT = ~127ms, Mean Throughput = ~66 tokens/sec, 100% adversarial deflection (5/5 deflected).
  - Full project test suite running clean at 47/47 backend tests + 9/9 frontend tests (56/56 total passing tests) with zero static typing errors under `mypy` across 22 source files.
- `FEAT-005-VERIFY` executed and 100% completed:
  - All 4 Acceptance Criteria (AC-1 through AC-4) verified and signed off.
  - Checklists in `context/feature-specs/FEAT-005-VERIFY-eval-and-benchmarks.md` signed off.
  - Status updated in `context/feature-specs/INDEX.md` to `☑ Done`.
  - Comprehensive SQA verification test report generated in `feature-test-reports/FEAT-005-test-report.md`.


