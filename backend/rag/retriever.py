"""Real-time Vector Retriever with thread-pool execution and graceful fallbacks.

Embeds queries asynchronously on CPU, retrieves top-k chunks from CPUVectorStore,
enforces similarity thresholds, and guarantees resilient sub-second fallbacks.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, List, Optional, Tuple

# Suppress TensorFlow logging if TF was imported
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from backend.contracts import CitationItem, DocumentChunk, RetrievalResult
from backend.rag.cache import QueryCache
from backend.rag.vector_store import CPUVectorStore

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Retrieves grounded document chunks for user queries with caching and fallbacks."""

    def __init__(
        self,
        vector_store: CPUVectorStore,
        model_name: str = "all-MiniLM-L6-v2",
        cache_size: int = 128,
    ) -> None:
        self.vector_store = vector_store
        self.model_name = model_name
        self.cache = QueryCache(capacity=cache_size)
        self._model: Optional[Any] = None

    def _get_model(self) -> Any:
        """Lazily load SentenceTransformer model on CPU."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device="cpu")
        return self._model

    def warmup(self) -> None:
        """Eagerly load model and perform a warm-up encode to prime PyTorch JIT on CPU."""
        model = self._get_model()
        model.encode("warmup query", normalize_embeddings=True)

    def _sync_search(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Synchronous embedding and cosine similarity search executed in worker thread."""
        model = self._get_model()
        query_embedding = model.encode(query, normalize_embeddings=True)
        query_vector = [float(v) for v in query_embedding]
        return self.vector_store.search(
            query_embedding=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
        )

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.45,
        timeout_seconds: float = 1.0,
    ) -> RetrievalResult:
        """Asynchronously retrieve relevant document chunks within a strict timeout.
        
        Args:
            query: User question or search query string.
            top_k: Minimum number of candidate chunks (k >= 3).
            score_threshold: Minimum cosine similarity score threshold (default: 0.45).
            timeout_seconds: Hard deadline for retrieval before triggering fallback (1.0s).
            
        Returns:
            RetrievalResult containing chunks, citations, latency, and fallback state.
        """
        clean_query = query.strip()
        if not clean_query:
            return RetrievalResult(
                query=query,
                chunks=[],
                citations=[],
                retrieval_ms=0.0,
                from_cache=False,
                is_fallback=True,
            )

        # 1. Check LRU query cache
        cached = self.cache.get(clean_query)
        if cached is not None:
            return cached

        # 2. Asynchronous retrieval wrapped in strict timeout
        start_time = time.perf_counter()
        try:
            loop = asyncio.get_running_loop()
            raw_matches = await asyncio.wait_for(
                loop.run_in_executor(None, self._sync_search, clean_query, top_k, score_threshold),
                timeout=timeout_seconds,
            )
        except (asyncio.TimeoutError, Exception) as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("Retrieval fallback triggered for query '%s': %s", clean_query, e)
            return RetrievalResult(
                query=clean_query,
                chunks=[],
                citations=[],
                retrieval_ms=round(elapsed_ms, 2),
                from_cache=False,
                is_fallback=True,
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # 3. Check if any matches passed score threshold
        if not raw_matches:
            fallback_result = RetrievalResult(
                query=clean_query,
                chunks=[],
                citations=[],
                retrieval_ms=round(elapsed_ms, 2),
                from_cache=False,
                is_fallback=True,
            )
            self.cache.put(clean_query, fallback_result)
            return fallback_result

        # 4. Construct grounded chunks and citations
        chunks: List[DocumentChunk] = []
        citations: List[CitationItem] = []

        for chunk, score in raw_matches:
            chunks.append(chunk)
            snippet = chunk.content[:200].strip()
            if len(chunk.content) > 200:
                snippet += "..."
            citations.append(
                CitationItem(
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    section_header=chunk.section_header,
                    score=round(score, 4),
                    snippet=snippet,
                )
            )

        result = RetrievalResult(
            query=clean_query,
            chunks=chunks,
            citations=citations,
            retrieval_ms=round(elapsed_ms, 2),
            from_cache=False,
            is_fallback=False,
        )

        # 5. Populate LRU cache
        self.cache.put(clean_query, result)
        return result
