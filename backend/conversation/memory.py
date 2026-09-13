"""Sliding-window memory manager for multi-turn conversation sessions.

Enforces strict context window bounds per FEAT-002-BE by truncating older conversation
turns while preserving the latest N turns without dropping system prompt context.
"""

from typing import List

from backend.contracts import ChatMessage


def prune_messages(messages: List[ChatMessage], max_turns: int = 6) -> List[ChatMessage]:
    """Prunes conversation history to a sliding window of recent message turns.

    Each turn consists of a user message and an assistant response (2 messages).
    Therefore, max_turns=6 retains at most 12 messages. If the history exceeds
    this limit, earlier turns are discarded from the head of the list.

    Args:
        messages: Chronological list of ChatMessage instances in the session.
        max_turns: Maximum number of conversation turns to retain (default: 6).

    Returns:
        List[ChatMessage]: Bounded list containing at most max_turns * 2 messages.
    """
    if max_turns <= 0 or not messages:
        return []

    max_messages = max_turns * 2
    if len(messages) <= max_messages:
        return list(messages)

    return list(messages[-max_messages:])
