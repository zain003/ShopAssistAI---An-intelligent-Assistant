# Test Report: FEAT-002 — Conversation Manager & Prompt Orchestrator

**Feature ID:** `FEAT-002-BE`  
**Spec Reference:** `context/feature-specs/FEAT-002-BE-prompt-orchestrator.md`  
**Verification Ref:** `context/feature-specs/FEAT-002-VERIFY-prompt-orchestrator.md`  
**Date Tested:** `2026-09-13`  
**SQA Status:** `PASSED`  
**Tester:** `SQA Automation Agent`  

---

## 1. Executive Summary

| Total Test Cases | Passed | Failed | Skipped | Pass Rate | SQA Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **13** | **13** | `0` | `0` | `100%` | **PASSED** |

> **SQA Gate Policy:** Zero failing tests allowed. 100% pass rate achieved across all unit tests and static type checks.

---

## 2. Test Environment & Tools

- **Python Version:** 3.12.10 / 3.14.3
- **Test Runner:** `pytest 9.0.3` / `9.1.1` with `pytest-asyncio 1.4.0`
- **Type Checker:** `mypy 2.3.1` (Strict mode, zero issues)
- **Host OS:** Windows

---

## 3. Acceptance Criteria Traceability Matrix

| AC ID | Acceptance Criterion | Test Name in `tests/test_conversation.py` | Status |
| :--- | :--- | :--- | :---: |
| **AC-1** | `build_chat_payload()` outputs system prompt at index 0 followed strictly by alternating turns | `test_build_chat_payload_structure` | `PASS` |
| **AC-2** | Number of conversation history messages in payload never exceeds 12 (6 turns) | `test_build_chat_payload_history_never_exceeds_12_messages`, `test_sliding_window_prunes_older_turns` | `PASS` |
| **AC-3** | System prompt explicitly contains out-of-domain deflection directive | `test_system_prompt_contains_deflection_directive` | `PASS` |
| **AC-4** | Session reset zeroes message array and clears `active_order_id` and customer entities | `test_reset_session_clears_messages_and_entities` | `PASS` |
| **AC-5** | Zero external tool or RAG dependencies present (in-memory pure prompt orchestration) | `test_zero_cloud_and_zero_tool_dependencies` | `PASS` |

---

## 4. Multi-Layer Test Execution Results

### 4.1 Unit Test Execution (`pytest tests/test_conversation.py -v`)

```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\zaina\Desktop\nlp-assignment-01
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 13 items

tests/test_conversation.py::test_get_or_create_session_creates_new_id_when_none PASSED [  7%]
tests/test_conversation.py::test_get_or_create_session_persists_existing_session PASSED [ 15%]
tests/test_conversation.py::test_order_id_extracted_and_persisted PASSED [ 23%]
tests/test_conversation.py::test_customer_email_extracted_and_persisted PASSED [ 30%]
tests/test_conversation.py::test_sliding_window_prunes_older_turns PASSED [ 38%]
tests/test_conversation.py::test_system_prompt_contains_required_xml_tags PASSED [ 46%]
tests/test_conversation.py::test_system_prompt_contains_deflection_directive PASSED [ 53%]
tests/test_conversation.py::test_system_prompt_injects_active_order_focus PASSED [ 61%]
tests/test_conversation.py::test_reset_session_clears_messages_and_entities PASSED [ 69%]
tests/test_conversation.py::test_build_chat_payload_structure PASSED     [ 76%]
tests/test_conversation.py::test_build_chat_payload_history_never_exceeds_12_messages PASSED [ 84%]
tests/test_conversation.py::test_stale_session_cleanup PASSED            [ 92%]
tests/test_conversation.py::test_zero_cloud_and_zero_tool_dependencies PASSED [100%]

============================= 13 passed in 0.12s ==============================
```

### 4.2 Static Type Checking (`mypy`)

```text
mypy backend/conversation tests/test_conversation.py
Success: no issues found in 6 source files
```

---

## 5. Edge Cases & Boundary Analysis

| Scenario | Input / Trigger | Expected Outcome | Verified |
| :--- | :--- | :--- | :---: |
| **New Session Auto-ID** | `get_or_create_session(None)` | Generates prefixed unique UUID `sess_*` with timestamp | `YES` |
| **Natural Order ID Extraction** | User types `"Can you check on order #1002?"` | Regex extracts and normalizes to `ORD-1002` | `YES` |
| **Explicit Order ID Extraction** | User types `"Where is my package for ORD-1085?"` | Regex extracts `ORD-1085` and updates `active_order_id` | `YES` |
| **Customer Email Extraction** | User types `"My email is emily.zhang@example.com"` | Regex binds `active_customer_email` | `YES` |
| **History Overflow (15 turns)** | 30 user/assistant messages added | History is trimmed to exactly 12 messages (6 turns) | `YES` |
| **Active Order XML Injection** | Session has `active_order_id="ORD-1085"` | Prompt dynamically renders `<active_session_order>` block | `YES` |
| **Session Reset Cleanup** | Calling `reset_session()` | Clears messages, active order, email, and turns | `YES` |
| **Stale Session TTL Eviction** | Inactive session exceeds TTL (3600s) | Inactive session automatically evicted from memory | `YES` |
| **Zero Cloud / RAG Invariant** | Inspect module imports | No langchain, chromadb, openai, or pinecone imported | `YES` |

---

## 6. Defects Discovered & Resolved

No defects identified during SQA cycle.

---

## 7. SQA Sign-Off & Recommendation

- [x] **100% Test Pass Rate Achieved (13/13 tests)**
- [x] **Zero Unresolved Defects**
- [x] **Strict Mypy Type Checking Clean**
- [x] **Zero Cloud LLM Invocations or Vector DB Lookups**
- [x] **Feature Ready for Merge / Next Feature Transition (`FEAT-003-BE`)**

**Final SQA Verdict:** **APPROVED (PASSED 100%)**
