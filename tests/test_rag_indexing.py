"""Unit tests for FEAT-006: Offline Indexing Pipeline & Document Corpus."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator
import pytest

from backend.contracts import DocumentMetadata, DocumentChunk
from backend.rag.chunker import chunk_markdown_document, estimate_tokens
from backend.rag.vector_store import CPUVectorStore
from backend.rag.indexer import DocumentIndexer


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a clean temporary directory for isolated test indexing."""
    tmp = tempfile.mkdtemp(prefix="shopassist_rag_test_")
    path = Path(tmp)
    yield path
    shutil.rmtree(tmp, ignore_errors=True)


def test_load_documents_discovers_markdown_files() -> None:
    """Verifies loader scans data/documents/ and generates valid DocumentMetadata with SHA-256."""
    indexer = DocumentIndexer(docs_dir="data/documents", store_dir="data/vector_store")
    documents = indexer.load_documents()

    assert len(documents) >= 50, f"Expected >= 50 documents, got {len(documents)}"
    for doc in documents:
        assert isinstance(doc, DocumentMetadata)
        assert doc.doc_id, "doc_id must be non-empty"
        assert doc.title, "title must be non-empty"
        assert doc.category in ["policies", "shipping", "products", "warranties", "troubleshooting", "payments", "general"]
        assert len(doc.doc_hash) == 64, "doc_hash must be a 64-char SHA-256 hex string"
        assert Path(doc.source_path).exists(), f"Source path {doc.source_path} does not exist"


def test_chunk_documents_preserves_headers() -> None:
    """Verifies chunks retain doc title and section heading, with bounded character lengths."""
    doc_meta = DocumentMetadata(
        doc_id="test_return_policy",
        title="Test Return Policy",
        category="policies",
        source_path="dummy.md",
        doc_hash="a" * 64,
        created_at=1000.0,
    )
    sample_text = """# Test Return Policy

## 30-Day Policy Overview
Customers may return items within 30 days of receiving their shipment for a full refund.
All merchandise must be in original condition with packaging intact and labels attached.

## Exceptions and Exclusions
Opened consumables, software products, and gift cards are strictly non-returnable.
"""

    chunks = chunk_markdown_document(doc_meta, sample_text, chunk_size=300, chunk_overlap=40)
    assert len(chunks) >= 2, "Expected at least 2 chunks from multiple sections"

    for chunk in chunks:
        assert isinstance(chunk, DocumentChunk)
        assert chunk.doc_id == "test_return_policy"
        assert chunk.title == "Test Return Policy"
        assert chunk.section_header in ["30-Day Policy Overview", "Exceptions and Exclusions", "Overview", "General"]
        assert len(chunk.content) >= 80, f"Chunk too small: {len(chunk.content)}"
        assert len(chunk.content) <= 500, f"Chunk exceeded bound: {len(chunk.content)}"
        assert chunk.token_count > 0


def test_hash_cache_skips_unchanged_documents(temp_dir: Path) -> None:
    """Verifies re-running index_corpus skips unchanged files and reports 0 newly embedded documents."""
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    store_dir = temp_dir / "store"
    store_dir.mkdir()

    # Create 2 test markdown documents
    doc1 = docs_dir / "doc1.md"
    doc1.write_text("# Doc One\n\n## Section A\nThis is content for document one with enough text to make a valid chunk.", encoding="utf-8")
    doc2 = docs_dir / "doc2.md"
    doc2.write_text("# Doc Two\n\n## Section B\nThis is content for document two with enough text to make a valid chunk.", encoding="utf-8")

    indexer = DocumentIndexer(docs_dir=str(docs_dir), store_dir=str(store_dir))

    # First run: indexes both docs
    result1 = indexer.index_corpus(force_rebuild=False)
    assert result1["total_docs"] == 2
    assert result1["new_docs"] == 2
    assert result1["skipped_docs"] == 0

    # Second run immediately after without modifications: 0 newly embedded
    result2 = indexer.index_corpus(force_rebuild=False)
    assert result2["total_docs"] == 2
    assert result2["new_docs"] == 0
    assert result2["skipped_docs"] == 2
    assert result2["rebuilt"] is False


def test_index_corpus_persists_vector_index_to_disk(temp_dir: Path) -> None:
    """Verifies vector store directory contains persisted index files after run."""
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    store_dir = temp_dir / "store"
    store_dir.mkdir()

    doc_file = docs_dir / "sample.md"
    doc_file.write_text(
        "# Fast Shipping\n\n## Delivery Times\nWe ship all standard orders within 24 business hours using FedEx.",
        encoding="utf-8",
    )

    indexer = DocumentIndexer(docs_dir=str(docs_dir), store_dir=str(store_dir))
    result = indexer.index_corpus(force_rebuild=True)

    assert result["total_docs"] == 1
    assert result["total_chunks"] >= 1

    chunks_file = store_dir / "chunks.json"
    manifest_file = store_dir / "index_manifest.json"
    np_file = store_dir / "embeddings.npy"

    assert chunks_file.exists(), "chunks.json must exist on disk"
    assert manifest_file.exists(), "index_manifest.json must exist on disk"
    assert np_file.exists(), "embeddings.npy must exist on disk"

    # Verify reloading from disk
    loaded_store = CPUVectorStore(embedding_dim=384)
    loaded_store.load(str(store_dir))
    assert loaded_store.size() == result["total_chunks"]


def test_corrupted_file_logs_warning_and_continues(temp_dir: Path) -> None:
    """Verifies an unreadable or non-markdown file does not raise an unhandled exception or abort pipeline."""
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    store_dir = temp_dir / "store"
    store_dir.mkdir()

    # Valid doc
    valid_file = docs_dir / "valid.md"
    valid_file.write_text("# Valid Document\n\n## Content\nProper content for testing.", encoding="utf-8")

    # Empty 0-byte file
    empty_file = docs_dir / "empty.md"
    empty_file.write_bytes(b"")

    # Non-UTF8 corrupted bytes file
    bad_bytes_file = docs_dir / "corrupted.md"
    bad_bytes_file.write_bytes(b"\x80\x81\xff\xfe\xab\xcd")

    indexer = DocumentIndexer(docs_dir=str(docs_dir), store_dir=str(store_dir))
    docs = indexer.load_documents()

    # Pipeline continues smoothly and loads valid document while safely ignoring bad files
    assert len(docs) == 1
    assert docs[0].doc_id == "valid"

    # Indexing completes without crash
    result = indexer.index_corpus(force_rebuild=False)
    assert result["total_docs"] == 1
    assert result["total_chunks"] >= 1


def test_embedding_dimension_is_384(temp_dir: Path) -> None:
    """Verifies all generated embeddings match all-MiniLM-L6-v2 dimension (384)."""
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    store_dir = temp_dir / "store"
    store_dir.mkdir()

    doc_file = docs_dir / "dim_test.md"
    doc_file.write_text("# Dimension Verification\n\n## Check\nEnsures dense vector length is exactly 384.", encoding="utf-8")

    indexer = DocumentIndexer(docs_dir=str(docs_dir), store_dir=str(store_dir))
    docs = indexer.load_documents()
    chunks = indexer.chunk_documents(docs)
    embedded = indexer.generate_embeddings(chunks)

    assert len(embedded) >= 1
    for chunk in embedded:
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 384, f"Expected 384 dimensions, got {len(chunk.embedding)}"
