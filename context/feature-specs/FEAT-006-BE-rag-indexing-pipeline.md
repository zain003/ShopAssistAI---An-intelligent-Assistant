# FEAT-006-BE — Offline Indexing Pipeline & Document Corpus (P0)

**Layer**: Backend  
**Goal**: Build an offline, re-runnable indexing pipeline that loads 50–100 e-commerce markdown documents, chunks them with header-aware boundaries, computes local CPU embeddings via `all-MiniLM-L6-v2`, and persists the index to a CPU vector store with hash-based incremental update detection.

---

## Depends on / Context pack / Consumes
**Depends on**: `context/feature-specs/000-shared-contracts.md`  
**Context pack**:
```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class DocumentMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    doc_id: str
    title: str
    category: str
    source_path: str
    doc_hash: str
    created_at: float

class DocumentChunk(BaseModel):
    model_config = ConfigDict(frozen=True)
    chunk_id: str
    doc_id: str
    title: str
    section_header: str
    content: str
    token_count: int
    char_count: int
    chunk_index: int
    embedding: Optional[List[float]] = None
```
**Consumes**: `DocumentMetadata`, `DocumentChunk` from `000-shared-contracts.md`.

---

## Provides / Exposes
```python
class DocumentIndexer:
    def __init__(
        self,
        docs_dir: str = "data/documents",
        store_dir: str = "data/vector_store",
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None: ...
    def load_documents(self) -> List[DocumentMetadata]: ...
    def chunk_documents(
        self,
        documents: List[DocumentMetadata],
        chunk_size: int = 400,
        chunk_overlap: int = 50,
    ) -> List[DocumentChunk]: ...
    def generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]: ...
    def index_corpus(self, force_rebuild: bool = False) -> Dict[str, Any]: ...
```

---

## Scope
- **Scope (In)**:
  - Document corpus directory (`data/documents/`) structured with 50–100 markdown files across 6 domains: return policies, shipping tiers, product user manuals, warranty specs, order troubleshooting, and store payment FAQs.
  - Header-aware chunking strategy: parses markdown `#` and `##` headings, producing chunks bounded between 300 and 500 characters (~80–120 tokens) with 50-character overlap.
  - Local CPU embedding generation using `all-MiniLM-L6-v2` (384-dimensional dense vectors).
  - CPU vector store persistence (`data/vector_store/`) supporting cosine similarity indexing.
  - Re-runnable SHA-256 fingerprint registry: documents with identical SHA-256 hashes are not re-embedded on subsequent runs unless `--rebuild` is supplied.
  - Command-line entrypoint `scripts/index_documents.py` returning exit code 0 upon index completion.
- **Scope (Out)**:
  - Online query vector similarity search (covered in `FEAT-007-BE`).
  - WebSocket protocol and frontend citation badges (covered in `FEAT-008-FE`).

---

## Tech & Files to Touch
- `data/documents/` — Corpus of 50–100 Markdown knowledge files.
- `backend/rag/chunker.py` — Markdown header splitter and token estimator.
- `backend/rag/vector_store.py` — Local CPU vector store interface and disk persistence.
- `backend/rag/indexer.py` — Document loading, hashing, embedding generation, and incremental indexing logic.
- `scripts/index_documents.py` — CLI runner script for offline index generation.
- `tests/test_rag_indexing.py` — Unit tests for loading, chunking, hashing, and index persistence.

---

## Tests to Write FIRST
1. `test_load_documents_discovers_markdown_files`: Verifies loader scans `data/documents/` and generates valid `DocumentMetadata` with SHA-256 hashes.
2. `test_chunk_documents_preserves_headers`: Verifies chunks retain doc title and section heading, with length bounded between 100 and 500 characters.
3. `test_hash_cache_skips_unchanged_documents`: Verifies re-running `index_corpus(force_rebuild=False)` skips unchanged files and reports 0 newly embedded documents.
4. `test_index_corpus_persists_vector_index_to_disk`: Verifies vector store directory contains persisted index files after run.
5. `test_corrupted_file_logs_warning_and_continues`: Verifies an unreadable or non-markdown file does not raise an unhandled exception or abort pipeline.

---

## Implementation Steps
1. Create `data/documents/` with 50–100 domain Markdown files categorized into subdirectories (`policies/`, `products/`, `shipping/`, `warranties/`, `troubleshooting/`).
2. Implement `backend/rag/chunker.py` with `chunk_markdown_document` maintaining header context and sliding-window character boundaries.
3. Implement `backend/rag/vector_store.py` providing `add_chunks`, `save(path)`, `load(path)`, and cosine distance calculation on CPU.
4. Implement `backend/rag/indexer.py` with `DocumentIndexer` orchestrating file scanning, SHA-256 diffing against `index_manifest.json`, batch CPU embedding generation, and vector store write.
5. Implement `scripts/index_documents.py` with `--docs-dir`, `--store-dir`, and `--rebuild` flags.
6. Verify pipeline reproducibility by running `python scripts/index_documents.py` twice consecutively and verifying zero redundant computation on second run.

---

## Acceptance Criteria
- [ ] Document corpus contains at least 50 markdown files with valid frontmatter or headings.
- [ ] Chunks are produced with non-empty `doc_id`, `title`, and `section_header` attributes.
- [ ] All generated vector embeddings have exactly 384 dimensions.
- [ ] Running indexing script twice without document modifications performs 0 new embedding calls on second execution.
- [ ] Running script with `--rebuild` re-embeds all documents and overwrites vector store cleanly.
- [ ] Total offline indexing of 50–100 documents completes on CPU in under 120 seconds.

---

## Definition of Done
- [ ] Automated tests in `tests/test_rag_indexing.py` pass 100%.
- [ ] Mypy strict type checking clean across `backend/rag/`.
- [ ] Corpus count verified at >= 50 documents.
- [ ] Test report generated in `feature-test-reports/FEAT-006-test-report.md`.
- [ ] `context/feature-specs/INDEX.md` updated.

---

## Edge Cases to Handle
- **Empty Document**: Files with 0 bytes are skipped with logged warning.
- **Single Huge Paragraph**: Markdown files lacking headers are chunked by fixed character window with overlap.
- **Non-ASCII Characters**: Unicode symbols and smart quotes handled without UTF-8 decode errors.
- **Corrupted Store**: If disk index file is truncated, indexer rebuilds from scratch rather than crashing.

---

## Pre-flight Check
Before starting, confirm `FEAT-005-VERIFY` passed. If not, stop and flag instead of proceeding.

---

## What's Next
- `FEAT-006-VERIFY-rag-indexing-pipeline.md`
- `FEAT-007-BE-rag-retrieval-grounding.md`

---

## Ambiguity Resolution Protocol
If you encounter a case not covered by this spec:
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log it in `context/feature-specs/DEVIATIONS.md` as: `[FEAT-006-BE] — [what was ambiguous] — [assumption made]`
4. Continue implementation; do not block on it unless it affects the data model defined in `000-shared-contracts.md`, in which case STOP and flag for human review.
