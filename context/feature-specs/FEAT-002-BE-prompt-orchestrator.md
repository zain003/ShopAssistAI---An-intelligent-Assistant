# FEAT-002-BE — Conversation Manager & Prompt Orchestrator (P0)

**Layer**: Backend  
**Goal**: Manage in-memory multi-turn conversation sessions, implement sliding-window memory management, and construct structured XML system prompts embedding domain persona, catalog specs, mock orders, and deflection rules without tools or RAG.

---

## Depends on / Context pack / Consumes
**Depends on**: `context/feature-specs/000-shared-contracts.md`  
**Context pack**:
```python
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from enum import Enum

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True)
    role: Role
    content: str
    timestamp: float

class SessionState(BaseModel):
    session_id: str
    created_at: float
    last_active_at: float
    messages: List[ChatMessage]
    active_order_id: Optional[str]
    total_turns: int
```
**Consumes**: `SessionState`, `ChatMessage`, `Role` from `000-shared-contracts.md`.

---

## Provides / Exposes
```python
class ConversationManager:
    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionState: ...
    def add_user_message(self, session_id: str, content: str) -> ChatMessage: ...
    def add_assistant_message(self, session_id: str, content: str) -> ChatMessage: ...
    def reset_session(self, session_id: str) -> SessionState: ...
    def build_chat_payload(
        self,
        session_id: str,
        max_history_turns: int = 6
    ) -> List[Dict[str, str]]: ...
```

---

## Scope
- **Scope (In)**:
  - In-memory session store mapping `session_id` to `SessionState`.
  - Entity extraction regex for order numbers matching `ORD-\d{4}` stored in `active_order_id`.
  - Sliding-window memory: retains only latest `max_history_turns * 2` messages.
  - Prompt orchestrator injecting structured XML sections: `<store_persona>`, `<catalog_products>`, `<mock_orders>`, `<store_policies>`, `<deflection_rules>`.
- **Scope (Out)**:
  - Direct network I/O or LLM inference calls (owned by `FEAT-001-BE`).
  - WebSocket framing and client dispatch (owned by `FEAT-003-BE`).

---

## Tech & Files to Touch
- `backend/conversation/data.py` — Static mock orders (`ORD-1001` to `ORD-1005`), catalog items, return/shipping policies.
- `backend/conversation/memory.py` — Sliding-window history truncation logic.
- `backend/conversation/orchestrator.py` — Structured XML prompt template builder.
- `backend/conversation/manager.py` — `ConversationManager` session state coordinator.
- `tests/test_conversation.py` — Unit tests for session lifecycle, memory pruning, and prompt generation.

---

## Tests to Write FIRST
1. `test_get_or_create_session_creates_new_id_when_none`: Empty session_id -> returns fresh SessionState with valid UUID.
2. `test_order_id_extracted_and_persisted`: User message containing `"Where is ORD-1085?"` -> sets `session.active_order_id == "ORD-1085"`.
3. `test_sliding_window_prunes_older_turns`: Add 16 messages (8 turns) -> `build_chat_payload` includes exactly 1 system prompt + 12 recent history messages.
4. `test_system_prompt_contains_required_xml_tags`: Verify system message content contains `<store_persona>`, `<catalog_products>`, `<mock_orders>`, `<store_policies>`.
5. `test_reset_session_clears_messages_and_entities`: Resetting session wipes message history and sets `active_order_id = None`.

---

## Implementation Steps
1. Create `backend/conversation/data.py` populating 5 mock orders, 6 catalog products, and 30-day return policy terms.
2. Create `backend/conversation/memory.py` implementing `prune_messages(messages, max_turns=6)`.
3. Create `backend/conversation/orchestrator.py` defining `render_system_prompt(active_order_id=None)` with XML tags and explicit out-of-domain deflection instructions.
4. Create `backend/conversation/manager.py` implementing `ConversationManager` with thread-safe session dictionary and regex order extraction.

---

## Acceptance Criteria
- [ ] `build_chat_payload()` outputs system prompt as index 0 followed strictly by alternating user/assistant turns.
- [ ] Number of conversation history messages in payload never exceeds 12 (6 turns).
- [ ] System prompt explicitly includes the instruction: *"If the query is outside products, orders, returns, or shipping, politely refuse and redirect to store support."*
- [ ] Session reset zeroes the message array and clears `active_order_id`.
- [ ] No external database or network dependency exists in this module.

---

## Definition of Done
- [ ] Unit tests pass 100% (`pytest tests/test_conversation.py`).
- [ ] Zero linting errors under `flake8` or `ruff`.
- [ ] Strict type annotations on all methods verified with `mypy`.

---

## Edge Cases to Handle
- Malformed order format: user types "order 1085" -> regex should recognize both `ORD-1085` and `1085` as matching candidate.
- Memory overflow: session receiving 100+ turns must not cause memory leak or crash.
- Stale session garbage collection: sessions inactive for > 1 hour discarded cleanly.

---

## Pre-flight Check
Confirm `FEAT-001-VERIFY-llm-engine.md` passes and `000-shared-contracts.md` is present.

---

## What's Next
- `FEAT-002-VERIFY-prompt-orchestrator.md` — Verification pass.
- `FEAT-003-BE-websocket-api.md` — FastAPI WebSocket streaming endpoint.

---

## Ambiguity Resolution Protocol
If you encounter a case not covered by this spec:
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log it in `context/feature-specs/DEVIATIONS.md` as: `[FEAT-002-BE] — [what was ambiguous] — [assumption made]`.
4. Continue implementation; do not block unless it alters `000-shared-contracts.md`.
