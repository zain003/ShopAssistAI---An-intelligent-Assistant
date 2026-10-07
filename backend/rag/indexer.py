"""Offline Document Indexer and Corpus Ingestion Pipeline for ShopAssist AI.

Scans data/documents/, chunks markdown files with header preservation, generates
384-dimensional dense vectors with SentenceTransformer (all-MiniLM-L6-v2), and
persists index with SHA-256 fingerprint caching for incremental updates.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Suppress TensorFlow logging if TF was imported
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from backend.contracts import DocumentChunk, DocumentMetadata
from backend.rag.chunker import chunk_markdown_document
from backend.rag.vector_store import CPUVectorStore

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Manages document corpus scanning, chunking, embedding, and vector index caching."""

    def __init__(
        self,
        docs_dir: str = "data/documents",
        store_dir: str = "data/vector_store",
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.docs_dir = Path(docs_dir)
        self.store_dir = Path(store_dir)
        self.model_name = model_name
        self.vector_store = CPUVectorStore(embedding_dim=384)
        self._model: Optional[Any] = None

    def _get_embedding_model(self) -> Any:
        """Lazily initialize the local SentenceTransformer embedding model on CPU."""
        if self._model is None:
            logger.info("Initializing SentenceTransformer('%s') on CPU...", self.model_name)
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device="cpu")
        return self._model

    def load_documents(self) -> List[DocumentMetadata]:
        """Scan docs_dir recursively and extract DocumentMetadata with SHA-256 hashes."""
        if not self.docs_dir.exists():
            logger.warning("Documents directory %s does not exist", self.docs_dir)
            return []

        documents: List[DocumentMetadata] = []

        # Recursively discover all markdown files
        for file_path in sorted(self.docs_dir.rglob("*.md")):
            try:
                # Check empty file
                if file_path.stat().st_size == 0:
                    logger.warning("Skipping 0-byte file: %s", file_path)
                    continue

                raw_bytes = file_path.read_bytes()
                try:
                    content = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    logger.warning("Skipping non-UTF8 file: %s", file_path)
                    continue

                if not content.strip():
                    logger.warning("Skipping whitespace-only file: %s", file_path)
                    continue

                # Compute content SHA-256 hash
                doc_hash = hashlib.sha256(raw_bytes).hexdigest()

                # Derive doc_id from stem (e.g. return_policy)
                doc_id = file_path.stem

                # Derive category from immediate parent folder name
                category = file_path.parent.name if file_path.parent != self.docs_dir else "general"

                # Extract title from first H1 line if present
                title = doc_id.replace("_", " ").title()
                title_match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()

                documents.append(
                    DocumentMetadata(
                        doc_id=doc_id,
                        title=title,
                        category=category,
                        source_path=str(file_path),
                        doc_hash=doc_hash,
                        created_at=file_path.stat().st_mtime,
                    )
                )
            except Exception as e:
                logger.warning("Error processing file %s: %s", file_path, e)
                continue

        logger.info("Loaded %d valid documents from %s", len(documents), self.docs_dir)
        return documents

    def chunk_documents(
        self,
        documents: List[DocumentMetadata],
        chunk_size: int = 400,
        chunk_overlap: int = 50,
    ) -> List[DocumentChunk]:
        """Segment a list of documents into header-aware chunks."""
        all_chunks: List[DocumentChunk] = []

        for doc in documents:
            try:
                file_path = Path(doc.source_path)
                if not file_path.exists():
                    logger.warning("Source path %s no longer exists", doc.source_path)
                    continue
                text = file_path.read_text(encoding="utf-8")
                doc_chunks = chunk_markdown_document(
                    doc_meta=doc,
                    text=text,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                all_chunks.extend(doc_chunks)
            except Exception as e:
                logger.warning("Failed to chunk document %s: %s", doc.doc_id, e)
                continue

        logger.info("Generated %d chunks from %d documents", len(all_chunks), len(documents))
        return all_chunks

    def generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Generate 384-dimensional dense vectors for chunks using SentenceTransformer on CPU."""
        if not chunks:
            return []

        model = self._get_embedding_model()
        texts = [c.content for c in chunks]

        logger.info("Generating embeddings for %d chunks on CPU...", len(texts))
        raw_embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        embedded_chunks: List[DocumentChunk] = []
        for i, chunk in enumerate(chunks):
            vector: List[float] = [float(v) for v in raw_embeddings[i]]
            # Reconstruct with embedding vector populated
            embedded_chunks.append(
                DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    section_header=chunk.section_header,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    char_count=chunk.char_count,
                    chunk_index=chunk.chunk_index,
                    embedding=vector,
                )
            )

        return embedded_chunks

    def index_corpus(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Run incremental or full offline indexing pass.
        
        Args:
            force_rebuild: If True, discards existing cache and re-indexes all docs.
            
        Returns:
            Dictionary with telemetry and execution summary.
        """
        start_time = time.perf_counter()
        self.store_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = self.store_dir / "index_manifest.json"

        documents = self.load_documents()
        total_docs = len(documents)

        # Load existing manifest if present and valid
        existing_manifest: Dict[str, Any] = {}
        if not force_rebuild and manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    existing_manifest = json.load(f)
            except Exception as e:
                logger.warning("Failed reading manifest at %s: %s. Rebuilding.", manifest_file, e)
                existing_manifest = {}

        cached_docs: Dict[str, str] = existing_manifest.get("doc_hashes", {})

        # Determine which documents have changed or are new
        docs_to_embed: List[DocumentMetadata] = []
        for doc in documents:
            if force_rebuild or doc.doc_id not in cached_docs or cached_docs[doc.doc_id] != doc.doc_hash:
                docs_to_embed.append(doc)

        # If no documents changed, try loading the existing vector store
        if not docs_to_embed and not force_rebuild:
            try:
                self.vector_store.load(str(self.store_dir))
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info("All %d documents unchanged. Reused cached index.", total_docs)
                return {
                    "total_docs": total_docs,
                    "new_docs": 0,
                    "skipped_docs": total_docs,
                    "total_chunks": self.vector_store.size(),
                    "rebuilt": False,
                    "duration_ms": round(elapsed_ms, 2),
                }
            except Exception as e:
                logger.warning("Cached store corrupted (%s), executing full rebuild.", e)
                docs_to_embed = documents

        # Re-index documents
        self.vector_store.clear()
        chunks = self.chunk_documents(documents)
        embedded_chunks = self.generate_embeddings(chunks)
        self.vector_store.add_chunks(embedded_chunks)
        self.vector_store.save(str(self.store_dir))

        # Write updated manifest
        new_manifest = {
            "model_name": self.model_name,
            "embedding_dim": 384,
            "total_documents": total_docs,
            "total_chunks": len(embedded_chunks),
            "doc_hashes": {doc.doc_id: doc.doc_hash for doc in documents},
            "last_indexed_at": time.time(),
        }
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(new_manifest, f, indent=2)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Index corpus finished: %d docs, %d chunks in %.2fms",
            total_docs,
            len(embedded_chunks),
            elapsed_ms,
        )

        return {
            "total_docs": total_docs,
            "new_docs": len(docs_to_embed),
            "skipped_docs": total_docs - len(docs_to_embed),
            "total_chunks": len(embedded_chunks),
            "rebuilt": force_rebuild or len(docs_to_embed) == total_docs,
            "duration_ms": round(elapsed_ms, 2),
        }
