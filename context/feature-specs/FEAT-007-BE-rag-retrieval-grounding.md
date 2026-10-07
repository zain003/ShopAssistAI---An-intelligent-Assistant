# FEAT-007-BE — Real-Time Vector Retrieval, Prompt Grounding & Failure Handling (P0)

**Layer**: Backend  
**Goal**: Integrate asynchronous vector retrieval into the Conversation Manager, retrieving top-k (k >= 3) relevant chunks, caching repeated queries, injecting grounded knowledge into prompt context within a 500-token budget, and handling all Phase IV failure modes without hanging or crashing.

---

## Depends on / Context pack / Consumes
**Depends on**: `context/feature-specs/000-shared-contracts.md`, `context/feature-specs/FEAT-002-BE-prompt-orchestrator.md`, `context/feature-specs/FEAT-006-BE-rag-indexing-pipeline.md`  
**Context pack**:
```python
from typing import List, Optional, Dict, Tuple, Any
from pydantic import BaseModel, ConfigDict

class CitationItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    doc_id: str
    title: str
    section_header: str
    score: float
    snippet: str

class RetrievalResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    query: str
    chunks: List[Any]
    citations: List[CitationItem]
    retrieval_ms: float
    from_cache: bool = False
    is_fallback: bool = False
```
**Consumes**: `DocumentChunk`, `RetrievalResult`, `CitationItem` from `000-shared-contracts.md`; `DocumentIndexer` from `FEAT-006-BE`; `ConversationManager` from `FEAT-002-BE`.

---

## Provides / Exposes
```python
class VectorRetriever:
    def __init__(self, vector_store: Any, model_name: str = "all-MiniLM-L6-v2", cache_size: int = 128) -> None: ...
    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.45,
        timeout_seconds: float = 1.0,
    ) -> RetrievalResult: ...

class RAGConversationManager:
    def __init__(self, base_manager: Any, retriever: VectorRetriever) -> None: ...
    async def build_rag_chat_payload(
        self,
        session_id: str,
        user_query: str,
        max_context_tokens: int = 500,
    ) -> Tuple[List[Dict[str, str]], RetrievalResult]: ...
```

---

## Scope
- **Scope (In)**:
  - Asynchronous query embedding executed in thread pool executor (`asyncio.to_thread` / loop executor) to avoid blocking the asyncio event loop.
  - Top-k cosine similarity search returning minimum 3 relevant chunks with confidence scores in [0.0, 1.0].
  - LRU in-memory query cache storing up to 128 query embeddings and retrieval results.
  - Strict prompt injection: formats chunks into `<retrieved_context>` XML block containing document title, section header, and content.
  - Hard token budgeting: caps `<retrieved_context>` at 500 tokens; trims lowest-similarity chunks if over budget.
  - Phase IV Failure Handling:
    1. *No relevant matches*: If all retrieved chunks score < `score_threshold` (0.45), marks `is_fallback=True`, omits context injection, and directs LLM to state missing knowledge politely.
    2. *Retrieval infrastructure timeout/error*: Wraps search in 1.0s timeout; on timeout or store exception, logs warning, marks `is_fallback=True`, and continues dialogue ungrounded.
    3. *Context overflow*: Dynamically truncates conversation history window if combined prompt exceeds 1,500 tokens.
- **Scope (Out)**:
  - Document chunking and offline index building (handled in `FEAT-006-BE`).
  - Frontend client DOM rendering of citations (handled in `FEAT-008-FE`).

---

## Tech & Files to Touch
- `backend/rag/retriever.py` — Asynchronous vector retriever and score threshold evaluator.
- `backend/rag/cache.py` — LRU query cache implementation.
- `backend/conversation/orchestrator.py` — XML prompt builder extension for `<retrieved_context>`.
- `backend/conversation/manager.py` — Async pipeline hooking retrieval into chat payload creation.
- `tests/test_rag_retrieval.py` — Unit tests for retrieval, caching, budgeting, and fallbacks.

---

## Tests to Write FIRST
1. `test_retrieve_returns_top_k_chunks_with_scores`: Verifies query returns at least 3 chunks sorted by descending cosine score.
2. `test_query_cache_avoids_recomputation`: Verifies subsequent query with identical text sets `from_cache=True` and resolves in < 5ms.
3. `test_low_similarity_query_triggers_fallback`: Verifies out-of-domain query with score < 0.45 sets `is_fallback=True` and empty citations.
4. `test_retrieval_timeout_triggers_fallback_without_exception`: Simulates vector store delay > 1.0s; asserts returns fallback `RetrievalResult` without throwing.
5. `test_context_budget_caps_injected_tokens_under_500`: Verifies prompt orchestrator enforces 500-token ceiling on `<retrieved_context>`.

---

## Implementation Steps
1. Create `backend/rag/cache.py` with thread-safe `QueryCache` (fixed capacity 128, LRU eviction).
2. Implement `backend/rag/retriever.py` with `VectorRetriever.retrieve()` wrapping embedding and similarity search in `asyncio.to_thread` with `asyncio.wait_for(timeout=1.0)`.
3. Add score threshold comparison: discard chunks with score < `score_threshold`. If 0 chunks remain, set `is_fallback=True`.
4. Update `backend/conversation/orchestrator.py` to inject `<retrieved_context>` with doc metadata when `is_fallback=False`.
5. Integrate `RAGConversationManager` in `backend/conversation/manager.py` returning prompt payload and `RetrievalResult`.
6. Add unit test suite in `tests/test_rag_retrieval.py`.

---

## Acceptance Criteria
- [ ] Query retrieval returns at least 3 chunks when relevant matches exist.
- [ ] Query cache hit returns stored result in less than 10 milliseconds.
- [ ] When similarity score is below 0.45, `is_fallback` is True and no irrelevant chunks are injected.
- [ ] Retrieval timeout (1.0s) or vector store exception returns fallback payload without dropping connection.
- [ ] Total tokens in `<retrieved_context>` section do not exceed 500 tokens.
- [ ] Average retrieval latency on CPU is under 500 milliseconds for cold queries.

---

## Definition of Done
- [ ] All unit tests in `tests/test_rag_retrieval.py` pass 100%.
- [ ] Mypy strict type checking clean.
- [ ] Zero unhandled exceptions on simulated vector store disconnect.
- [ ] SQA test report generated in `feature-test-reports/FEAT-007-test-report.md`.
- [ ] `context/feature-specs/INDEX.md` updated.

---

## Edge Cases to Handle
- **Empty Query String**: Returns fallback result immediately without invoking embedding model.
- **Identical Repeated Queries**: Served instantaneously from LRU cache.
- **Massive Retrieved Chunks**: Truncated strictly at 500-token boundary without breaking prompt XML tags.
- **Corrupted Embeddings File**: Caught gracefully and routed to fallback conversation path.

---

## Pre-flight Check
Before starting, confirm `FEAT-006-VERIFY` passed. If not, stop and flag instead of proceeding.

---

## What's Next
- `FEAT-007-VERIFY-rag-retrieval-grounding.md`
- `FEAT-008-FE-rag-citations-ui.md`

---

## Ambiguity Resolution Protocol
If you encounter a case not covered by this spec:
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log it in `context/feature-specs/DEVIATIONS.md` as: `[FEAT-007-BE] — [what was ambiguous] — [assumption made]`
4. Continue implementation; do not block on it unless it affects the data model defined in `000-shared-contracts.md`, in which case STOP and flag for human review.
