# Progress Tracker

## Current Phase

- **Phase II (Local LLM Engine)**: Complete. Implemented `LLMEngine` with async streaming, readiness probing, warmup, and TTFT/throughput telemetry.
- **Next Phase**: Implementation of `FEAT-002-BE` (Conversation Manager & Prompt Orchestration).

---

## Current Goal

- Implement and verify the conversation manager, prompt orchestrator, and FastAPI WebSocket server.

---

## Milestones & Status

| Phase | Milestone Name                                | Status        | Notes / Artifacts                                |
| :---: | :-------------------------------------------- | :-----------: | :----------------------------------------------- |
| **I** | Business Case & Flow Design                   | **Completed** | `context/project-overview.md`                    |
| **-** | Context & Feature Specs Definition            | **Completed** | `context/` & `context/feature-specs/`            |
| **II**| Local LLM Setup & CPU Engine (`FEAT-001`)     | **Completed** | `FEAT-001-BE` + `FEAT-001-VERIFY`: 13/13 tests passed, SQA approved |
| **III**| Conversation Manager & Memory (`FEAT-002`)   | Not Started   | Sliding window, XML prompt builder, domain guards|
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

