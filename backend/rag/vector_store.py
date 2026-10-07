"""Local CPU Vector Store for ShopAssist domain document embeddings.

Provides in-memory cosine similarity indexing, persistent JSON and NumPy storage,
and sub-millisecond retrieval on multi-core CPU hardware.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.contracts import DocumentChunk

logger = logging.getLogger(__name__)


class CPUVectorStore:
    """In-memory dense vector store with cosine similarity search on CPU."""

    def __init__(self, embedding_dim: int = 384) -> None:
        self.embedding_dim = embedding_dim
        self._chunks: List[DocumentChunk] = []
        self._chunk_map: Dict[str, DocumentChunk] = {}
        self._embeddings: Optional[np.ndarray] = None  # Shape (N, D), float32 normalized

    def size(self) -> int:
        """Return the number of indexed chunks."""
        return len(self._chunks)

    def clear(self) -> None:
        """Clear all indexed chunks and embeddings."""
        self._chunks.clear()
        self._chunk_map.clear()
        self._embeddings = None

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks and their dense embeddings to the index.
        
        Args:
            chunks: List of DocumentChunk instances with embedding populated.
        """
        valid_chunks: List[DocumentChunk] = []
        embeddings_list: List[List[float]] = []

        for chunk in chunks:
            if chunk.embedding is None:
                logger.warning("Skipping chunk %s without embedding", chunk.chunk_id)
                continue
            if len(chunk.embedding) != self.embedding_dim:
                raise ValueError(
                    f"Chunk {chunk.chunk_id} embedding dimension mismatch: "
                    f"expected {self.embedding_dim}, got {len(chunk.embedding)}"
                )
            valid_chunks.append(chunk)
            embeddings_list.append(chunk.embedding)

        if not valid_chunks:
            return

        new_embeddings = np.array(embeddings_list, dtype=np.float32)
        # Normalize vectors for fast cosine similarity via dot product
        norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        new_embeddings_normalized = new_embeddings / norms

        if self._embeddings is None:
            self._embeddings = new_embeddings_normalized
            self._chunks = valid_chunks
            self._chunk_map = {c.chunk_id: c for c in valid_chunks}
        else:
            self._embeddings = np.vstack([self._embeddings, new_embeddings_normalized])
            for c in valid_chunks:
                if c.chunk_id in self._chunk_map:
                    # Update existing chunk
                    idx = next(i for i, ch in enumerate(self._chunks) if ch.chunk_id == c.chunk_id)
                    self._chunks[idx] = c
                else:
                    self._chunks.append(c)
                self._chunk_map[c.chunk_id] = c

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        score_threshold: float = 0.0,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Perform cosine similarity search on CPU against indexed vectors.
        
        Args:
            query_embedding: Dense embedding vector for query (length 384).
            top_k: Maximum number of chunks to return.
            score_threshold: Minimum cosine similarity score threshold (0.0 to 1.0).
            
        Returns:
            List of (DocumentChunk, score) tuples sorted in descending order of score.
        """
        if self._embeddings is None or len(self._chunks) == 0:
            return []

        if len(query_embedding) != self.embedding_dim:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self.embedding_dim}, got {len(query_embedding)}"
            )

        query_vec = np.array(query_embedding, dtype=np.float32)
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec /= norm
        else:
            return []

        # Cosine similarity is dot product of L2-normalized vectors
        scores = np.dot(self._embeddings, query_vec)

        # Get top-k indices sorted by descending score
        sorted_indices = np.argsort(scores)[::-1]

        results: List[Tuple[DocumentChunk, float]] = []
        for idx in sorted_indices:
            score = float(scores[idx])
            if score < score_threshold:
                break
            results.append((self._chunks[idx], score))
            if len(results) >= top_k:
                break

        return results

    def save(self, directory: str) -> None:
        """Persist the vector store and chunk metadata to disk.
        
        Args:
            directory: Directory path where index files will be stored.
        """
        store_path = Path(directory)
        store_path.mkdir(parents=True, exist_ok=True)

        chunks_data: List[Dict[str, Any]] = [c.model_dump() for c in self._chunks]
        chunks_file = store_path / "chunks.json"
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2)

        if self._embeddings is not None:
            np_file = store_path / "embeddings.npy"
            np.save(np_file, self._embeddings)

        logger.info("Saved %d chunks to %s", len(self._chunks), store_path)

    def load(self, directory: str) -> None:
        """Load vector store and chunk metadata from disk.
        
        Args:
            directory: Directory path containing chunks.json and embeddings.npy.
        """
        store_path = Path(directory)
        chunks_file = store_path / "chunks.json"
        np_file = store_path / "embeddings.npy"

        if not chunks_file.exists():
            raise FileNotFoundError(f"Vector store chunks file not found at {chunks_file}")

        try:
            with open(chunks_file, "r", encoding="utf-8") as f:
                raw_chunks = json.load(f)
            chunks = [DocumentChunk(**c) for c in raw_chunks]

            embeddings = None
            if np_file.exists():
                embeddings = np.load(np_file)
            elif chunks and chunks[0].embedding is not None:
                embeddings = np.array([c.embedding for c in chunks], dtype=np.float32)

            if embeddings is not None:
                # Re-normalize just in case
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1e-10
                self._embeddings = (embeddings / norms).astype(np.float32)
            else:
                self._embeddings = None

            self._chunks = chunks
            self._chunk_map = {c.chunk_id: c for c in chunks}
            logger.info("Loaded %d chunks from %s", len(self._chunks), store_path)
        except Exception as e:
            logger.error("Failed to load vector store from %s: %s", directory, e)
            raise
