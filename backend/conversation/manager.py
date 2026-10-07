"""In-memory conversation manager and session coordinator for ShopAssist AI.

Manages session lifecycle, turns, entity extraction, sliding-window memory,
and payload construction for LLM inference per FEAT-002-BE.
"""

from __future__ import annotations

import re
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.contracts import ChatMessage, RetrievalResult, Role, SessionState
from backend.conversation.memory import prune_messages
from backend.conversation.orchestrator import format_retrieved_context, render_system_prompt

# Regex patterns for entity extraction
ORDER_ID_PATTERN = re.compile(r"\bORD-(\d{4})\b", re.IGNORECASE)
NATURAL_ORDER_PATTERN = re.compile(
    r"\b(?:order|package|tracking|invoice)\s*(?:#|no\.?|num\.?|number)?\s*(\d{4})\b",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


class ConversationManager:
    """Coordinates active chat sessions, turn state, and memory budgets."""

    def __init__(self, session_ttl_seconds: float = 3600.0) -> None:
        """Initializes the in-memory conversation manager.

        Args:
            session_ttl_seconds: Max seconds of inactivity before a session is purged.
        """
        self._sessions: Dict[str, SessionState] = {}
        self._session_ttl_seconds = session_ttl_seconds
        self._lock = threading.Lock()

    def _cleanup_stale_sessions(self, current_time: float) -> None:
        """Purges sessions inactive beyond the configured TTL threshold.

        Args:
            current_time: Current epoch timestamp.
        """
        stale_ids = [
            sid
            for sid, session in self._sessions.items()
            if (current_time - session.last_active_at) > self._session_ttl_seconds
        ]
        for sid in stale_ids:
            self._sessions.pop(sid, None)

    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionState:
        """Retrieves an existing session or creates a new session state.

        Args:
            session_id: Optional string session ID. If None, a new UUID is generated.

        Returns:
            SessionState instance for the requested or newly created session.
        """
        now = time.time()
        with self._lock:
            self._cleanup_stale_sessions(now)

            if not session_id or not session_id.strip():
                new_id = f"sess_{uuid.uuid4().hex[:12]}"
                session = SessionState(
                    session_id=new_id,
                    created_at=now,
                    last_active_at=now,
                    messages=[],
                    active_order_id=None,
                    active_customer_email=None,
                    topic_history=[],
                    total_turns=0,
                )
                self._sessions[new_id] = session
                return session

            cleaned_id = session_id.strip()
            if cleaned_id in self._sessions:
                session = self._sessions[cleaned_id]
                session.last_active_at = now
                return session

            session = SessionState(
                session_id=cleaned_id,
                created_at=now,
                last_active_at=now,
                messages=[],
                active_order_id=None,
                active_customer_email=None,
                topic_history=[],
                total_turns=0,
            )
            self._sessions[cleaned_id] = session
            return session

    def _extract_entities(self, content: str, session: SessionState) -> None:
        """Extracts order numbers and email addresses from text and binds to session.

        Args:
            content: Raw user message text.
            session: Active SessionState instance to mutate.
        """
        # 1. Match explicit ORD-XXXX format
        match = ORDER_ID_PATTERN.search(content)
        if match:
            session.active_order_id = f"ORD-{match.group(1)}"
        else:
            # 2. Match natural "order 1085" or "order #1085" format
            natural_match = NATURAL_ORDER_PATTERN.search(content)
            if natural_match:
                session.active_order_id = f"ORD-{natural_match.group(1)}"

        # 3. Match customer email
        email_match = EMAIL_PATTERN.search(content)
        if email_match:
            session.active_customer_email = email_match.group(0).lower()

    def add_user_message(self, session_id: str, content: str) -> ChatMessage:
        """Appends a user turn message and updates entity bindings.

        Args:
            session_id: Session identifier string.
            content: User text content.

        Returns:
            ChatMessage: Newly created user message model.
        """
        session = self.get_or_create_session(session_id)
        now = time.time()

        with self._lock:
            self._extract_entities(content, session)
            message = ChatMessage(
                role=Role.USER,
                content=content.strip(),
                timestamp=now,
            )
            session.messages.append(message)
            session.last_active_at = now

        return message

    def add_assistant_message(self, session_id: str, content: str) -> ChatMessage:
        """Appends an assistant turn message and increments turn count.

        Args:
            session_id: Session identifier string.
            content: Assistant generated response text.

        Returns:
            ChatMessage: Newly created assistant message model.
        """
        session = self.get_or_create_session(session_id)
        now = time.time()

        with self._lock:
            message = ChatMessage(
                role=Role.ASSISTANT,
                content=content.strip(),
                timestamp=now,
            )
            session.messages.append(message)
            session.total_turns += 1
            session.last_active_at = now

        return message

    def reset_session(self, session_id: str) -> SessionState:
        """Resets conversation history and extracted entities for a session.

        Args:
            session_id: Session identifier string.

        Returns:
            SessionState: The reset session state with empty messages and entities.
        """
        session = self.get_or_create_session(session_id)
        now = time.time()

        with self._lock:
            session.messages.clear()
            session.active_order_id = None
            session.active_customer_email = None
            session.topic_history.clear()
            session.total_turns = 0
            session.last_active_at = now

        return session

    def build_chat_payload(
        self,
        session_id: str,
        max_history_turns: int = 6,
    ) -> List[Dict[str, str]]:
        """Constructs the LLM input payload with system prompt and sliding history.

        Ensures:
        1. System prompt is at index 0.
        2. History is bounded to at most max_history_turns * 2 messages (default 12).
        3. Roles strictly alternate or conform to standard chat formats.

        Args:
            session_id: Session identifier string.
            max_history_turns: Max turns (user+assistant pairs) to include in history.

        Returns:
            List[Dict[str, str]]: List of {'role': str, 'content': str} dictionaries.
        """
        session = self.get_or_create_session(session_id)

        with self._lock:
            system_prompt = render_system_prompt(active_order_id=session.active_order_id)
            pruned_messages = prune_messages(session.messages, max_turns=max_history_turns)

            payload: List[Dict[str, str]] = [
                {"role": Role.SYSTEM.value, "content": system_prompt}
            ]

            for msg in pruned_messages:
                payload.append({"role": msg.role.value, "content": msg.content})

        return payload


class RAGConversationManager:
    """Coordinates conversation sessions and grounds turns with real-time vector retrieval."""

    def __init__(self, base_manager: ConversationManager, retriever: Any) -> None:
        """Initializes the RAG conversation manager with an underlying ConversationManager and retriever."""
        self.base_manager = base_manager
        self.retriever = retriever

    async def build_rag_chat_payload(
        self,
        session_id: str,
        user_query: str,
        max_context_tokens: int = 500,
        max_history_turns: int = 6,
    ) -> Tuple[List[Dict[str, str]], RetrievalResult]:
        """Retrieves domain context, formats prompt, and returns chat payload + retrieval result.
        
        Args:
            session_id: Active session identifier.
            user_query: Current turn customer question.
            max_context_tokens: Token ceiling for retrieved document chunks (default: 500).
            max_history_turns: Maximum conversation turns to retain in sliding window.
            
        Returns:
            Tuple of (chat_payload, retrieval_result).
        """
        # 1. Asynchronously retrieve top-k chunks with score threshold and timeout
        retrieval_result = await self.retriever.retrieve(
            query=user_query,
            top_k=3,
            score_threshold=0.45,
            timeout_seconds=1.0,
        )

        # 2. Format retrieved context XML block capped at max_context_tokens
        context_xml = format_retrieved_context(retrieval_result, max_tokens=max_context_tokens)

        # 3. Assemble chat payload with grounded system prompt
        session = self.base_manager.get_or_create_session(session_id)
        with self.base_manager._lock:
            system_prompt = render_system_prompt(
                active_order_id=session.active_order_id,
                retrieved_context_xml=context_xml,
            )
            pruned_messages = prune_messages(session.messages, max_turns=max_history_turns)

            payload: List[Dict[str, str]] = [
                {"role": Role.SYSTEM.value, "content": system_prompt}
            ]
            for msg in pruned_messages:
                payload.append({"role": msg.role.value, "content": msg.content})

        return payload, retrieval_result
