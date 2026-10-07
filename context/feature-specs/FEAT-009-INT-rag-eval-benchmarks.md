# FEAT-009-INT — RAG Latency Benchmarks & Grounding Evaluation Suite (P1)

**Layer**: Integration  
**Goal**: Measure vector retrieval latency separately from generation time, evaluate multi-user concurrent query throughput, verify Phase IV failure handling, and validate factual response grounding against domain documents.

---

## Depends on / Context pack / Consumes
**Depends on**: `context/feature-specs/000-shared-contracts.md`, `context/feature-specs/FEAT-006-BE-rag-indexing-pipeline.md`, `context/feature-specs/FEAT-007-BE-rag-retrieval-grounding.md`, `context/feature-specs/FEAT-005-INT-eval-and-benchmarks.md`  
**Context pack**:
```python
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict

class RetrievalMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    total_retrieval_ms: float
    chunks_evaluated: int
    chunks_returned: int
    cache_hit: bool

class BenchmarkResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    run_index: int
    ttft_ms: float
    total_tokens: int
    total_duration_ms: float
    tokens_per_second: float
```
**Consumes**: `RetrievalMetrics`, `BenchmarkResult` from `000-shared-contracts.md`; `VectorRetriever` from `FEAT-007-BE`.

---

## Provides / Exposes
```python
class RAGBenchmarkRunner:
    def __init__(self, retriever: Any, llm_engine: Any) -> None: ...
    async def benchmark_retrieval_latency(self, queries: List[str], runs: int = 5) -> Dict[str, float]: ...
    async def benchmark_concurrency(self, queries: List[str], concurrent_clients: int = 5) -> Dict[str, float]: ...
    async def evaluate_grounding_fidelity(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]: ...
    async def evaluate_failure_handling(self) -> Dict[str, bool]: ...
    def generate_rag_evaluation_report(self) -> str: ...
```

---

## Scope
- **Scope (In)**:
  - Latency benchmark script `tests/benchmark_rag.py` measuring retrieval time separately from LLM TTFT and generation duration.
  - Concurrency test asserting 5 simultaneous WebSocket clients trigger RAG retrieval concurrently without thread locking or timeout errors.
  - Grounding fidelity evaluation: asserts grounded answers include specific facts from indexed documents that ungrounded prompts do not contain.
  - Phase IV Failure evaluation: validates correct fallback triggers for:
    1. Zero relevance / out-of-domain queries.
    2. Simulated vector store latency exceeding 1.0s.
    3. Context budget overflow exceeding 1,500 prompt tokens.
  - Automated report generation outputting Markdown metrics to `feature-test-reports/FEAT-009-test-report.md`.
- **Scope (Out)**:
  - Chat interface UI layout or CSS styling (handled in `FEAT-008-FE`).

---

## Tech & Files to Touch
- `tests/benchmark_rag.py` — CLI benchmark runner for retrieval and generation latency.
- `tests/eval_rag_grounding.py` — Factual grounding and failure mode harness.
- `tests/test_rag_eval.py` — Automated pytest integration suite.
- `feature-test-reports/FEAT-009-test-report.md` — Generated SQA test report.

---

## Tests to Write FIRST
1. `test_benchmark_measures_retrieval_under_one_second`: Verifies mean retrieval latency across test queries is < 1000ms.
2. `test_concurrent_retrieval_does_not_deadlock`: Verifies 5 concurrent async retrieval tasks complete within 3 seconds.
3. `test_grounding_evaluator_verifies_source_citation`: Verifies responses to policy questions reference the matching document title.
4. `test_failure_mode_evaluator_confirms_fallback_on_irrelevant_query`: Verifies out-of-domain prompt emits `is_fallback=True` without hallucination.
5. `test_export_report_writes_markdown_to_feature_reports`: Verifies report file is written to disk with execution tables.

---

## Implementation Steps
1. Create `tests/benchmark_rag.py` measuring separate retrieval duration and token generation duration across 5 domain queries.
2. Implement concurrent runner in `tests/benchmark_rag.py` dispatching 5 parallel retrieval tasks with `asyncio.gather`.
3. Create `tests/eval_rag_grounding.py` with 5 domain grounding prompts and 3 adversarial/irrelevant prompts.
4. Implement failure test suite verifying graceful fallback under artificial delays and score thresholds.
5. Create markdown report serializer matching `feature-test-reports/template-test-report.md`.
6. Wire test suite into `tests/test_rag_eval.py`.

---

## Acceptance Criteria
- [ ] Average vector retrieval latency is under 1,000 milliseconds on CPU hardware.
- [ ] Concurrency test with 5 simultaneous requests completes without connection timeouts or errors.
- [ ] Grounding fidelity reaches 100% on standard store policy and product manual test questions.
- [ ] 100% of tested out-of-domain or low-similarity queries trigger fallback without crashing.
- [ ] Automated execution script exits with code 0 upon passing all evaluation thresholds.

---

## Definition of Done
- [ ] All tests in `tests/test_rag_eval.py` pass 100%.
- [ ] Mypy strict type checking clean.
- [ ] Latency metrics and grounding report saved in `feature-test-reports/FEAT-009-test-report.md`.
- [ ] `context/feature-specs/INDEX.md` updated.

---

## Edge Cases to Handle
- **Simultaneous Cache Misses**: Multiple concurrent identical queries resolve cleanly without race conditions.
- **CPU Resource Throttling**: Benchmarks run with warm-up pass discarded to avoid cold-start skew.
- **Empty Retrieval Set**: Grounding evaluator treats zero-citation fallback as expected behavior for ungrounded prompts.

---

## Pre-flight Check
Before starting, confirm `FEAT-007-VERIFY` and `FEAT-008-VERIFY` passed. If not, stop and flag instead of proceeding.

---

## What's Next
- `FEAT-009-VERIFY-rag-eval-benchmarks.md`
- Final Assignment 2 Documentation & Submission

---

## Ambiguity Resolution Protocol
If you encounter a case not covered by this spec:
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log it in `context/feature-specs/DEVIATIONS.md` as: `[FEAT-009-INT] — [what was ambiguous] — [assumption made]`
4. Continue implementation; do not block on it unless it affects the data model defined in `000-shared-contracts.md`, in which case STOP and flag for human review.
