# FEAT-003-VERIFY — Verification Pass: FastAPI WebSocket API (P0)

**Files being verified**: `FEAT-003-BE-websocket-api.md`

---

## 1. Test Suite Execution
Run the automated integration test suite for the FastAPI WebSocket API:
```bash
pytest tests/test_websocket.py -v
```

### Required Test Case Assertions
- [ ] `test_health_endpoint_returns_ok`: PASS
- [ ] `test_ws_connection_emits_session_created`: PASS
- [ ] `test_ws_user_message_streams_tokens_and_end`: PASS
- [ ] `test_ws_malformed_json_emits_error_frame`: PASS
- [ ] `test_ws_reset_session_emits_session_reset`: PASS

---

## 2. Acceptance Criteria Individual Re-Check
- [ ] AC-1: `/ws/chat` accepts connections and immediately returns `session_created`: **PASS/FAIL**
- [ ] AC-2: `user_message` results in sequential `token` frames ending with `stream_end`: **PASS/FAIL**
- [ ] AC-3: Invalid JSON emits structured error frame without dropping socket: **PASS/FAIL**
- [ ] AC-4: `reset_session` clears state and returns `session_reset`: **PASS/FAIL**
- [ ] AC-5: 5 concurrent connections run without cross-talk or blocking: **PASS/FAIL**

---

## 3. Definition of Done Compliance
- [ ] All integration tests pass 100%.
- [ ] Server starts cleanly with `uvicorn backend.api.main:app`.
- [ ] Zero unhandled exception tracebacks in server logs.
- [ ] Test report generated and committed in `feature-test-reports/FEAT-003-test-report.md`.

---

## 4. Remediation Rule
If any check fails:
1. Do NOT mark `FEAT-003-BE` complete.
2. Fix the bug in `backend/api/` immediately.
3. Re-run until 100% pass rate is achieved.
4. Update `context/feature-specs/INDEX.md` status only after full pass.
