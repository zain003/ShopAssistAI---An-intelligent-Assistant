# FEAT-001-VERIFY — Verification Pass: Local LLM Engine (P0)

**Files being verified**: `FEAT-001-BE-llm-engine.md`

---

## 1. Test Suite Execution
Run the automated unit test suite for the LLM engine:
```bash
pytest tests/test_llm_engine.py -v
```

### Required Test Case Assertions
- [ ] `test_engine_is_ready_true_on_200`: PASS
- [ ] `test_engine_is_ready_false_on_connection_error`: PASS
- [ ] `test_generate_stream_yields_tokens`: PASS
- [ ] `test_generate_stream_emits_telemetry_at_end`: PASS
- [ ] `test_generate_stream_raises_on_http_error`: PASS

---

## 2. Acceptance Criteria Individual Re-Check
- [ ] AC-1: `is_ready()` returns `True` if Ollama responds within 2.0s: **PASS/FAIL**
- [ ] AC-2: `generate_stream()` yields strings without buffering entire response: **PASS/FAIL**
- [ ] AC-3: Final yielded tuple has `StreamEndPayload` with `ttft_ms >= 0.0` and `tokens_per_second > 0.0`: **PASS/FAIL**
- [ ] AC-4: Unreachable Ollama host raises `LLMEngineError` with `code="SERVICE_UNAVAILABLE"`: **PASS/FAIL**
- [ ] AC-5: Zero external cloud API calls made: **PASS/FAIL**

---

## 3. Definition of Done Compliance
- [ ] All unit tests in `tests/test_llm_engine.py` pass 100% with zero warnings or errors.
- [ ] Strict type checking passes (`mypy backend/core/llm.py`).
- [ ] Code formatting and standards from `context/code-standards.md` verified.
- [ ] Test report generated and committed in `feature-test-reports/FEAT-001-test-report.md`.

---

## 4. Remediation Rule
If any check fails:
1. Do NOT mark `FEAT-001-BE` complete.
2. List the specific failure reason.
3. Fix the code in `backend/core/llm.py` immediately.
4. Re-run verification until 100% pass rate is achieved.
5. Update `context/feature-specs/INDEX.md` status only after full pass.
