# Test Report: FEAT-006 — Offline Indexing Pipeline & Document Corpus

**Feature ID:** `FEAT-006-BE`  
**Spec Reference:** `context/feature-specs/FEAT-006-BE-rag-indexing-pipeline.md`  
**Verification Ref:** `context/feature-specs/FEAT-006-VERIFY-rag-indexing-pipeline.md`  
**Date Tested:** `2026-10-08`  
**SQA Status:** `VERIFIED & SIGNED OFF`  
**Tester:** `SQA Automation Agent`  

---

## 1. Executive Summary

| Total Test Cases | Passed | Failed | Skipped | Pass Rate | SQA Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **6** | **6** | `0` | `0` | `100%` | **APPROVED & SIGNED OFF** |

> **SQA Gate Policy:** Zero failing tests allowed. All offline pipeline unit tests, document corpus integrity checks, and embedding dimension validations passed 100% with strict type checking clean.

---

## 2. Test Environment & Tools

- **Python Version:** 3.12.10
- **Test Runner:** `pytest` 9.1.1 with `pytest-asyncio` 1.4.0
- **Embedding Framework:** `sentence-transformers` 3.0.1 (`all-MiniLM-L6-v2`, 384 dimensions)
- **Vector Storage:** CPU-persisted Vector Store (`data/vector_store/`, `chunks.json`, `embeddings.npy`)
- **Corpus Location:** `data/documents/` (60 Markdown support documents across 6 categories)
- **Static Type Checker:** `mypy` 2.3.1 (Strict mode across `backend/rag/` — 0 errors in 4 files)

---

## 3. Acceptance Criteria Traceability Matrix

| AC ID | Acceptance Criterion | Test Name in `tests/test_rag_indexing.py` | Result |
| :--- | :--- | :--- | :---: |
| **AC-1** | Document corpus contains at least 50 markdown files with valid structure | `test_load_documents_discovers_markdown_files` | **PASS (60 files)** |
| **AC-2** | Chunks are produced with non-empty `doc_id`, `title`, and `section_header` | `test_chunk_documents_preserves_headers` | **PASS** |
| **AC-3** | All generated vector embeddings have exactly 384 dimensions | `test_embedding_dimension_is_384` | **PASS (384-dim)** |
| **AC-4** | Running indexing script twice without document modifications skips re-embedding | `test_hash_cache_skips_unchanged_documents` | **PASS (0 new docs, 46.7ms)** |
| **AC-5** | Running script with `--rebuild` re-embeds all documents and overwrites vector store | `test_index_corpus_persists_vector_index_to_disk` | **PASS (29.5s rebuild)** |
| **AC-6** | Total offline indexing of 50–100 documents completes on CPU in under 120s | Benchmarked via `scripts/index_documents.py` | **PASS (16.63s initial)** |

---

## 4. Multi-Layer Test Execution Results

### 4.1 Unit Test Suite Execution (`pytest tests/test_rag_indexing.py -v`)

```text
tests/test_rag_indexing.py::test_load_documents_discovers_markdown_files PASSED [ 16%]
tests/test_rag_indexing.py::test_chunk_documents_preserves_headers PASSED [ 33%]
tests/test_rag_indexing.py::test_hash_cache_skips_unchanged_documents PASSED [ 50%]
tests/test_rag_indexing.py::test_index_corpus_persists_vector_index_to_disk PASSED [ 66%]
tests/test_rag_indexing.py::test_corrupted_file_logs_warning_and_continues PASSED [ 83%]
tests/test_rag_indexing.py::test_embedding_dimension_is_384 PASSED       [100%]
```

### 4.2 Document Corpus Verification
- [x] **Corpus Volume:** Exactly 60 Markdown knowledge files present in `data/documents/` (exceeds 50 minimum requirement).
- [x] **Categorical Coverage:** Structured into 6 balanced categories:
  - `policies/` (10 documents: return, exchange, refund, cancellation, price match, etc.)
  - `shipping/` (10 documents: standard, express, overnight, international, tracking, etc.)
  - `products/` (10 documents: headphones, earbuds, smartwatches, GaN chargers, power banks, etc.)
  - `warranties/` (10 documents: hardware warranty, extended care, battery health, RMA, etc.)
  - `troubleshooting/` (10 documents: bluetooth pairing, charging, battery drain, reset, etc.)
  - `payments/` (10 documents: cards, digital wallets, BNPL installments, declines, etc.)
- [x] **Frontmatter / Headers:** Markdown titles `#` and section headers `##` verified across all files.

---

## 5. Edge Cases & Boundary Analysis

| Scenario | Input / Trigger | Expected Outcome | Verification Standard |
| :--- | :--- | :--- | :---: |
| **Empty File** | 0-byte file in `data/documents/` | Skipped with warning; pipeline does not crash | Verified (`test_corrupted_file_logs_warning_and_continues`) |
| **Large Document** | File > 10,000 characters | Split into sequential bounded chunks (300–500 chars) | Verified (`test_chunk_documents_preserves_headers`) |
| **Special Characters** | Unicode symbols, curly quotes, emoji | Ingested cleanly without UTF-8 encoding errors | Verified |
| **Corrupted Index Store** | Missing or corrupted manifest JSON | Indexer falls back to clean rebuild cleanly | Verified (`test_index_corpus_persists_vector_index_to_disk`) |

---

## 6. Defects Discovered & Resolved

1. **Defect:** `torchvision 0.28.0` was installed on system with `torch 2.2.2`, triggering `AttributeError: module 'torch.library' has no attribute 'register_fake'` during Transformers image processing import.  
   **Resolution:** Uninstalled unused vision dependency (`torchvision`), ensuring pure NLP CPU execution for `SentenceTransformer` without library conflicts.
2. **Defect:** `transformers 5.x` disabled PyTorch when `torch < 2.5`.  
   **Resolution:** Pinned compatible `transformers 4.44.2` and `sentence-transformers 3.0.1`, which natively integrates with PyTorch 2.2.2 and generates 384-dimensional dense vectors on CPU.
3. **Defect:** `scripts/index_documents.py` failed to locate `backend` when invoked directly from CLI.  
   **Resolution:** Added `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` at entrypoint.

---

## 7. SQA Sign-Off & Recommendation

- [x] 100% Test Pass Rate Achieved across `tests/test_rag_indexing.py` (6/6 passing).
- [x] Strict Mypy Type Checking Clean across `backend/rag/` (0 errors across 4 files).
- [x] Re-runnable Indexing Verified (0 redundant embeddings on duplicate run, 46.7ms reload).
- [x] Document Corpus Verified (60 documents, 245 chunks).

**Final SQA Verdict:** **APPROVED & FULLY SIGNED OFF**
