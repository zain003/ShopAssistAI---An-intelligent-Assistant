# Feature Specifications Index

This index tracks all feature specification files, their layer, build priority, dependencies, implementation status, and corresponding SQA verification reports.

---

## Master Feature Plan

| File ID | Layer | Priority | Feature Name | Depends On | Est. Lines | Status | Test Report |
| :--- | :---: | :---: | :--- | :--- | :---: | :---: | :--- |
| **`000-shared-contracts`** | CORE | P0 | Shared Data Models, Types & Envelopes | None | 130 | ☑ Done | N/A |
| **`FEAT-001-BE`** | Backend | P0 | Local LLM Engine & CPU Streaming Adapter | `000-shared-contracts` | 115 | ☑ Done | `feature-test-reports/FEAT-001-test-report.md` |
| **`FEAT-001-VERIFY`** | Verify | P0 | Verification Pass: LLM Engine | `FEAT-001-BE` | 75 | ☑ Done | `feature-test-reports/FEAT-001-test-report.md` |
| **`FEAT-002-BE`** | Backend | P0 | Conversation Manager & Prompt Orchestrator| `000-shared-contracts` | 130 | ☑ Done | `feature-test-reports/FEAT-002-test-report.md` |
| **`FEAT-002-VERIFY`** | Verify | P0 | Verification Pass: Dialogue & Memory | `FEAT-002-BE` | 75 | ☑ Done | `feature-test-reports/FEAT-002-test-report.md` |
| **`FEAT-003-BE`** | Backend | P0 | FastAPI WebSocket Streaming Endpoint | `FEAT-001-BE`, `FEAT-002-BE` | 135 | ☑ Done | `feature-test-reports/FEAT-003-test-report.md` |
| **`FEAT-003-VERIFY`** | Verify | P0 | Verification Pass: WebSocket API | `FEAT-003-BE` | 80 | ☑ Done | `feature-test-reports/FEAT-003-test-report.md` |
| **`FEAT-004-FE`** | Frontend| P0 | Web Chat UI & Real-Time Stream Renderer| `000-shared-contracts`, `FEAT-003-BE` | 135 | ☑ Done | `feature-test-reports/FEAT-004-test-report.md` |
| **`FEAT-004-VERIFY`** | Verify | P0 | Verification Pass: Web Chat UI | `FEAT-004-FE` | 75 | ☑ Done | `feature-test-reports/FEAT-004-test-report.md` |
| **`FEAT-005-INT`** | Integr. | P1 | Benchmark Suite & Adversarial Evaluator | `FEAT-001-BE`, `FEAT-003-BE` | 125 | ☑ Done | `feature-test-reports/FEAT-005-test-report.md` |
| **`FEAT-005-VERIFY`** | Verify | P1 | Verification Pass: Evaluation & Benchmarks| `FEAT-005-INT` | 75 | ☑ Done | `feature-test-reports/FEAT-005-test-report.md` |
| **`FEAT-006-BE`** | Backend | P0 | Offline Indexing Pipeline & Document Corpus | `000-shared-contracts` | 130 | ☑ Done | `feature-test-reports/FEAT-006-test-report.md` |
| **`FEAT-006-VERIFY`** | Verify | P0 | Verification Pass: RAG Indexing Pipeline | `FEAT-006-BE` | 75 | ☑ Done | `feature-test-reports/FEAT-006-test-report.md` |
| **`FEAT-007-BE`** | Backend | P0 | Real-Time Vector Retrieval & Grounding | `000-shared-contracts`, `FEAT-002-BE`, `FEAT-006-BE` | 135 | ☑ Done | `feature-test-reports/FEAT-007-test-report.md` |
| **`FEAT-007-VERIFY`** | Verify | P0 | Verification Pass: Vector Retrieval & Grounding | `FEAT-007-BE` | 75 | ☑ Done | `feature-test-reports/FEAT-007-test-report.md` |
| **`FEAT-008-FE`** | Frontend| P1 | Web Chat UI Citation Badges & Telemetry | `000-shared-contracts`, `FEAT-004-FE`, `FEAT-007-BE` | 125 | ☑ Done | `feature-test-reports/FEAT-008-test-report.md` |
| **`FEAT-008-VERIFY`** | Verify | P1 | Verification Pass: Citation UI & Telemetry | `FEAT-008-FE` | 75 | ☑ Done | `feature-test-reports/FEAT-008-test-report.md` |
| **`FEAT-009-INT`** | Integr. | P1 | RAG Latency Benchmarks & Grounding Eval | `FEAT-006-BE`, `FEAT-007-BE`, `FEAT-005-INT` | 130 | ☑ Done | `feature-test-reports/FEAT-009-test-report.md` |
| **`FEAT-009-VERIFY`** | Verify | P1 | Verification Pass: RAG Benchmarks & Eval | `FEAT-009-INT` | 75 | ☑ Done | `feature-test-reports/FEAT-009-test-report.md` |

---

## Status Legend
- ☐ Not Started
- ⏳ In Progress
- ☑ Verified & Done (100% Tests Passed & SQA Report Filed)
