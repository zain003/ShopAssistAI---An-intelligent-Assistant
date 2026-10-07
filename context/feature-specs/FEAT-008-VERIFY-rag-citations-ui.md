# FEAT-008-VERIFY — Verification Pass: Citation UI & Telemetry (P1)

**Files being verified**: `FEAT-008-FE-rag-citations-ui.md`

---

## 1. Test Suite Execution
Run the simulated DOM frontend test suite:
```bash
node tests/test_frontend.js
```

### Required Test Case Assertions
- [x] `test_stream_end_with_citations_renders_citation_badges`: PASS
- [x] `test_clicking_citation_badge_expands_snippet_drawer`: PASS
- [x] `test_stream_end_renders_retrieval_latency_in_telemetry_badge`: PASS
- [x] `test_fallback_turn_renders_general_mode_indicator`: PASS
- [x] `test_empty_citations_does_not_render_empty_citation_container`: PASS

---

## 2. Acceptance Criteria Individual Re-Check
- [x] AC-1: Grounded responses display at least one citation pill with document title and match percentage: **PASS**
- [x] AC-2: Clicking a citation pill toggles visibility of the excerpt drawer without page refresh: **PASS**
- [x] AC-3: Telemetry pill shows both `Retrieval:` and `TTFT:` values on completion of grounded turn: **PASS**
- [x] AC-4: Responses with zero citations display the fallback badge or omit container without DOM errors: **PASS**
- [x] AC-5: All interactive citation elements include keyboard focus styles and ARIA attributes: **PASS**

---

## 3. Definition of Done Compliance
- [x] All simulated DOM tests in `tests/test_frontend.js` pass 100%.
- [x] No layout regressions or broken message wrapping in `frontend/style.css`.
- [x] Accessible HTML markup with valid ARIA roles.
- [x] Test report generated and committed in `feature-test-reports/FEAT-008-test-report.md`.

---

## 4. Remediation Rule
If any check fails:
1. Do NOT mark `FEAT-008-FE` complete.
2. List the specific failure reason.
3. Fix the code in `frontend/` immediately.
4. Re-run verification until 100% pass rate is achieved.
5. Update `context/feature-specs/INDEX.md` status only after full pass.
