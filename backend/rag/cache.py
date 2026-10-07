"""Thread-safe LRU Query Cache for ShopAssist AI Vector Retrieval.

Caches query embeddings and retrieval results to provide sub-millisecond
responses for repeated customer questions.
"""

from __future__ import annotations

import collections
import threading
from typing import Optional
from backend.contracts import RetrievalResult


class QueryCache:
    """Thread-safe LRU cache for vector retrieval results."""

    def __init__(self, capacity: int = 128) -> None:
        self.capacity = capacity
        self._cache: collections.OrderedDict[str, RetrievalResult] = collections.OrderedDict()
        self._lock = threading.Lock()

    def _normalize_key(self, query: str) -> str:
        """Normalize query string for consistent cache key hashing."""
        return query.strip().lower()

    def get(self, query: str) -> Optional[RetrievalResult]:
        """Retrieve cached result if present, updating LRU order."""
        key = self._normalize_key(query)
        with self._lock:
            if key not in self._cache:
                return None
            # Move accessed key to end of OrderedDict (most recently used)
            self._cache.move_to_end(key)
            result = self._cache[key]
            # Return result marked as cache hit
            return RetrievalResult(
                query=result.query,
                chunks=result.chunks,
                citations=result.citations,
                retrieval_ms=0.5,
                from_cache=True,
                is_fallback=result.is_fallback,
            )

    def put(self, query: str, result: RetrievalResult) -> None:
        """Store retrieval result in cache, evicting oldest if capacity reached."""
        key = self._normalize_key(query)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = result
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)  # Evict least recently used

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Return count of currently cached queries."""
        with self._lock:
            return len(self._cache)
