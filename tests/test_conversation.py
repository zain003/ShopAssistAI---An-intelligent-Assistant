"""Unit tests for Conversation Manager, Memory Pruning, and Prompt Orchestration (FEAT-002-BE)."""

import time
from typing import List

import pytest

from backend.contracts import ChatMessage, Role
from backend.conversation import (
    CATALOG_PRODUCTS,
    DEFLECTION_DIRECTIVE,
    MOCK_ORDERS,
    ConversationManager,
    prune_messages,
    render_system_prompt,
)


def test_get_or_create_session_creates_new_id_when_none() -> None:
    """Empty session_id returns a fresh SessionState with a valid generated identifier."""
    manager = ConversationManager()
    session = manager.get_or_create_session(None)

    assert session is not None
    assert session.session_id.startswith("sess_")
    assert len(session.session_id) > 5
    assert session.messages == []
    assert session.active_order_id is None
    assert session.total_turns == 0
    assert session.created_at > 0.0
    assert session.last_active_at >= session.created_at


def test_get_or_create_session_persists_existing_session() -> None:
    """Retrieving with an existing session ID returns the exact same session instance."""
    manager = ConversationManager()
    sess1 = manager.get_or_create_session("my-custom-session")
    sess1.active_order_id = "ORD-1002"

    sess2 = manager.get_or_create_session("my-custom-session")
    assert sess2.session_id == "my-custom-session"
    assert sess2.active_order_id == "ORD-1002"


def test_order_id_extracted_and_persisted() -> None:
    """User message containing ORD-XXXX or natural 'order XXXX' extracts and persists the entity."""
    manager = ConversationManager()
    session = manager.get_or_create_session("sess-order-test")

    # 1. Standard ORD-XXXX format
    msg1 = manager.add_user_message("sess-order-test", "Where is my package for ORD-1085?")
    assert msg1.role == Role.USER
    assert session.active_order_id == "ORD-1085"

    # 2. Reset and test natural order format "order 1002"
    manager.reset_session("sess-order-test")
    assert session.active_order_id is None

    manager.add_user_message("sess-order-test", "Can you check on order #1002?")
    assert session.active_order_id == "ORD-1002"


def test_customer_email_extracted_and_persisted() -> None:
    """User message containing an email address binds to active_customer_email."""
    manager = ConversationManager()
    session = manager.get_or_create_session("sess-email-test")

    manager.add_user_message("sess-email-test", "My email is emily.zhang@example.com")
    assert session.active_customer_email == "emily.zhang@example.com"


def test_sliding_window_prunes_older_turns() -> None:
    """Adding 16 messages (8 turns) keeps only the 12 most recent messages (6 turns)."""
    messages: List[ChatMessage] = []
    t = time.time()

    for i in range(8):
        messages.append(ChatMessage(role=Role.USER, content=f"User question {i}", timestamp=t + i * 2))
        messages.append(ChatMessage(role=Role.ASSISTANT, content=f"Assistant answer {i}", timestamp=t + i * 2 + 1))

    assert len(messages) == 16

    pruned = prune_messages(messages, max_turns=6)
    assert len(pruned) == 12
    # Oldest turns 0 and 1 (first 4 messages) should have been pruned
    assert pruned[0].content == "User question 2"
    assert pruned[-1].content == "Assistant answer 7"


def test_system_prompt_contains_required_xml_tags() -> None:
    """Verify system message content contains all required XML domain tags."""
    prompt = render_system_prompt()

    assert "<store_persona>" in prompt
    assert "</store_persona>" in prompt
    assert "<catalog_products>" in prompt
    assert "</catalog_products>" in prompt
    assert "<mock_orders>" in prompt
    assert "</mock_orders>" in prompt
    assert "<store_policies>" in prompt
    assert "</store_policies>" in prompt
    assert "<deflection_rules>" in prompt
    assert "</deflection_rules>" in prompt

    # Verify catalog and orders are non-empty inside the prompt
    assert "SonicQuiet Elite Wireless Headphones" in prompt
    assert "ORD-1085" in prompt
    assert "Returns & Refunds" in prompt


def test_system_prompt_contains_deflection_directive() -> None:
    """Verify prompt explicitly contains the mandated out-of-domain deflection instructions."""
    prompt = render_system_prompt()

    assert "If the query is outside products, orders, returns, or shipping, politely refuse and redirect to store support." in prompt
    assert "I can only assist with questions regarding our store's products, orders, returns, and shipping policies." in prompt


def test_system_prompt_injects_active_order_focus() -> None:
    """When active_order_id is provided, the prompt injects an <active_session_order> block."""
    prompt_without_order = render_system_prompt(active_order_id=None)
    assert "<active_session_order" not in prompt_without_order

    prompt_with_order = render_system_prompt(active_order_id="ORD-1085")
    assert '<active_session_order id="ORD-1085">' in prompt_with_order
    assert "Emily Zhang" in prompt_with_order
    assert "FDX-992817264" in prompt_with_order


def test_reset_session_clears_messages_and_entities() -> None:
    """Resetting session wipes message history and sets active_order_id to None."""
    manager = ConversationManager()
    session_id = "sess-reset-target"

    manager.add_user_message(session_id, "Track ORD-1004 please")
    manager.add_assistant_message(session_id, "Order ORD-1004 is shipped.")

    session = manager.get_or_create_session(session_id)
    assert len(session.messages) == 2
    assert session.active_order_id == "ORD-1004"
    assert session.total_turns == 1

    reset_state = manager.reset_session(session_id)
    assert reset_state.messages == []
    assert reset_state.active_order_id is None
    assert reset_state.active_customer_email is None
    assert reset_state.topic_history == []
    assert reset_state.total_turns == 0


def test_build_chat_payload_structure() -> None:
    """build_chat_payload outputs system prompt at index 0 followed strictly by alternating turns."""
    manager = ConversationManager()
    session_id = "sess-payload-structure"

    manager.add_user_message(session_id, "Hello")
    manager.add_assistant_message(session_id, "Hello! How can I help you?")
    manager.add_user_message(session_id, "Do you sell headphones?")
    manager.add_assistant_message(session_id, "Yes, we have SonicQuiet Elite.")

    payload = manager.build_chat_payload(session_id, max_history_turns=6)

    # Index 0 is strictly system
    assert payload[0]["role"] == "system"
    assert "<store_persona>" in payload[0]["content"]

    # Trailing messages alternate correctly
    assert len(payload) == 5
    assert payload[1] == {"role": "user", "content": "Hello"}
    assert payload[2] == {"role": "assistant", "content": "Hello! How can I help you?"}
    assert payload[3] == {"role": "user", "content": "Do you sell headphones?"}
    assert payload[4] == {"role": "assistant", "content": "Yes, we have SonicQuiet Elite."}


def test_build_chat_payload_history_never_exceeds_12_messages() -> None:
    """Payload history messages never exceed 12 turns (24 messages capped at 12)."""
    manager = ConversationManager()
    session_id = "sess-long-conversation"

    for i in range(15):
        manager.add_user_message(session_id, f"User turn {i}")
        manager.add_assistant_message(session_id, f"Assistant turn {i}")

    payload = manager.build_chat_payload(session_id, max_history_turns=6)

    # Index 0 is system, plus 12 history messages = 13 items total
    assert len(payload) == 13
    assert payload[0]["role"] == "system"
    # History portion has exactly 12 items
    history_items = payload[1:]
    assert len(history_items) == 12
    assert history_items[0]["role"] == "user"
    assert history_items[0]["content"] == "User turn 9"
    assert history_items[-1]["role"] == "assistant"
    assert history_items[-1]["content"] == "Assistant turn 14"


def test_stale_session_cleanup() -> None:
    """Sessions inactive longer than TTL are purged automatically."""
    manager = ConversationManager(session_ttl_seconds=0.1)

    sess1 = manager.get_or_create_session("sess-stale-1")
    sess1.last_active_at = time.time() - 1.0  # Expired

    # Creating/retrieving triggers cleanup
    sess2 = manager.get_or_create_session("sess-active-2")
    assert "sess-stale-1" not in manager._sessions
    assert "sess-active-2" in manager._sessions


def test_zero_cloud_and_zero_tool_dependencies() -> None:
    """Ensures conversation and orchestrator modules do not import external cloud or agent libraries."""
    import sys
    forbidden_modules = ["langchain", "openai", "anthropic", "chromadb", "faiss", "pinecone"]
    for mod in forbidden_modules:
        assert mod not in sys.modules
