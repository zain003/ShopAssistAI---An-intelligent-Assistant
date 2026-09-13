# Progress Tracker

## Current Phase

- **Phase III (Conversation Manager & Memory)**: Completed. `FEAT-002-BE` and `FEAT-002-VERIFY` 100% verified (13/13 unit tests passed, SQA report filed).
- **Next Phase**: Implementation of `FEAT-003-BE` (FastAPI WebSocket Streaming Endpoint).

---

## Current Goal

- Implement and verify the FastAPI WebSocket streaming endpoint (`FEAT-003-BE` and `FEAT-003-VERIFY`).

---

## Milestones & Status

| Phase | Milestone Name                                | Status        | Notes / Artifacts                                |
| :---: | :-------------------------------------------- | :-----------: | :----------------------------------------------- |
| **I** | Business Case & Flow Design                   | **Completed** | `context/project-overview.md`                    |
| **-** | Context & Feature Specs Definition            | **Completed** | `context/` & `context/feature-specs/`            |
| **II**| Local LLM Setup & CPU Engine (`FEAT-001`)     | **Completed** | `FEAT-001-BE` + `FEAT-001-VERIFY`: 13/13 tests passed, SQA approved |
| **III**| Conversation Manager & Memory (`FEAT-002`)   | **Completed** | `FEAT-002-BE` + `FEAT-002-VERIFY`: 13/13 tests passed, SQA approved |
| **IV**| FastAPI WebSocket Streaming API (`FEAT-003`)  | Not Started   | `/ws/chat` JSON streaming endpoint               |
| **V** | Web Chat Interface (`FEAT-004`)               | Not Started   | Streaming UI, session reset, history view        |
| **VI**| SQA Tests, Benchmarks & Reports (`FEAT-005`)  | Not Started   | TTFT, tokens/sec, adversarial test reports       |

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
  - Ready for transition to Phase IV (`FEAT-003-BE`).



