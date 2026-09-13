"""Conversation and prompt orchestration module for ShopAssist AI."""

from backend.conversation.data import (
    CATALOG_PRODUCTS,
    DEFLECTION_DIRECTIVE,
    MOCK_ORDERS,
    STORE_PERSONA,
    STORE_POLICIES,
)
from backend.conversation.manager import ConversationManager
from backend.conversation.memory import prune_messages
from backend.conversation.orchestrator import render_system_prompt

__all__ = [
    "ConversationManager",
    "render_system_prompt",
    "prune_messages",
    "CATALOG_PRODUCTS",
    "MOCK_ORDERS",
    "STORE_PERSONA",
    "STORE_POLICIES",
    "DEFLECTION_DIRECTIVE",
]
