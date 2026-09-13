# FEAT-002-VERIFY — Verification Pass: Conversation Manager & Memory (P0)

**Files being verified**: `FEAT-002-BE-prompt-orchestrator.md`

---

## 1. Test Suite Execution
Run the automated unit test suite for conversation management and prompt orchestration:
```bash
pytest tests/test_conversation.py -v
```

### Required Test Case Assertions
- [x] `test_get_or_create_session_creates_new_id_when_none`: PASS
- [x] `test_order_id_extracted_and_persisted`: PASS
- [x] `test_sliding_window_prunes_older_turns`: PASS
- [x] `test_system_prompt_contains_required_xml_tags`: PASS
- [x] `test_reset_session_clears_messages_and_entities`: PASS

---

## 2. Acceptance Criteria Individual Re-Check
- [x] AC-1: `build_chat_payload()` outputs system prompt at index 0 followed strictly by alternating turns: **PASS**
- [x] AC-2: Number of conversation history messages never exceeds 12: **PASS**
- [x] AC-3: System prompt explicitly contains out-of-domain deflection directive: **PASS**
- [x] AC-4: Session reset zeroes message array and clears `active_order_id`: **PASS**
- [x] AC-5: Zero external tool or RAG dependencies present: **PASS**

---

## 3. Definition of Done Compliance
- [x] All unit tests in `tests/test_conversation.py` pass 100%.
- [x] Type check clean with `mypy backend/conversation/`.
- [x] Code standards verified against `context/code-standards.md`.
- [x] Test report generated and committed in `feature-test-reports/FEAT-002-test-report.md`.

---

## 4. Remediation Rule
If any check fails:
1. Do NOT mark `FEAT-002-BE` complete.
2. Fix the failure in `backend/conversation/` immediately.
3. Re-run until 100% pass rate.
4. Update `context/feature-specs/INDEX.md` status only after full pass.
