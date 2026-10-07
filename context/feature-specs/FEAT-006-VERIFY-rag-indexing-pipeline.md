# FEAT-006-VERIFY — Verification Pass: RAG Indexing Pipeline (P0)

**Files being verified**: `FEAT-006-BE-rag-indexing-pipeline.md`

---

## 1. Test Suite Execution
Run the automated test suite for the offline document indexing pipeline:
```bash
pytest tests/test_rag_indexing.py -v
```

### Required Test Case Assertions
- [x] `test_load_documents_discovers_markdown_files`: PASS
- [x] `test_chunk_documents_preserves_headers`: PASS
- [x] `test_hash_cache_skips_unchanged_documents`: PASS
- [x] `test_index_corpus_persists_vector_index_to_disk`: PASS
- [x] `test_corrupted_file_logs_warning_and_continues`: PASS

---

## 2. Acceptance Criteria Individual Re-Check
- [x] AC-1: Document corpus contains at least 50 markdown files with valid structure: **PASS**
- [x] AC-2: Chunks are produced with non-empty `doc_id`, `title`, and `section_header`: **PASS**
- [x] AC-3: All generated vector embeddings have exactly 384 dimensions: **PASS**
- [x] AC-4: Running indexing script twice consecutively performs 0 new embedding calls on second execution: **PASS**
- [x] AC-5: Running script with `--rebuild` re-embeds all documents and overwrites vector store: **PASS**
- [x] AC-6: Total offline indexing of 50–100 documents completes on CPU in under 120 seconds: **PASS**

---

## 3. Definition of Done Compliance
- [x] All unit tests in `tests/test_rag_indexing.py` pass 100% with zero warnings or errors.
- [x] Strict type checking passes (`mypy backend/rag/`).
- [x] Corpus verified in `data/documents/` with >= 50 files.
- [x] Test report generated and committed in `feature-test-reports/FEAT-006-test-report.md`.

---

## 4. Remediation Rule
If any check fails:
1. Do NOT mark `FEAT-006-BE` complete.
2. List the specific failure reason.
3. Fix the code in `backend/rag/` immediately.
4. Re-run verification until 100% pass rate is achieved.
5. Update `context/feature-specs/INDEX.md` status only after full pass.
