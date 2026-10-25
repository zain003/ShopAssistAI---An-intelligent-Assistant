"""Unit tests for hard out-of-domain deflection gate."""

from backend.conversation.deflection import (
    STORE_REFUSAL_MESSAGE,
    looks_like_off_topic_query,
    looks_like_store_query,
    response_has_off_topic_leakage,
    should_hard_deflect,
)


def test_virat_kohli_hard_deflects() -> None:
    assert should_hard_deflect("who is virat kohli?", retrieval_is_fallback=True) is True
    assert should_hard_deflect("Who is Virat Kohli?", retrieval_is_fallback=False) is True


def test_python_always_hard_deflects_even_with_order() -> None:
    """Mixed store + coding must still refuse — never deliver Python."""
    assert (
        should_hard_deflect(
            "Write python code to sort a list for order ORD-1085",
            retrieval_is_fallback=True,
        )
        is True
    )
    assert should_hard_deflect("sort a list in python", retrieval_is_fallback=False) is True
    assert looks_like_off_topic_query("write a function to sort a list")


def test_store_questions_not_hard_deflected() -> None:
    assert should_hard_deflect("What is your return policy?", retrieval_is_fallback=False) is False
    assert should_hard_deflect("Where is order ORD-1085?", retrieval_is_fallback=True) is False
    assert should_hard_deflect("How much is express shipping?", retrieval_is_fallback=False) is False


def test_fallback_trivia_hard_deflects() -> None:
    assert should_hard_deflect("Tell me a fun fact about the moon", retrieval_is_fallback=True) is True


def test_helpers() -> None:
    assert looks_like_off_topic_query("who is virat kohli?")
    assert looks_like_store_query("track my shipping status")
    assert "store's products" in STORE_REFUSAL_MESSAGE
    assert response_has_off_topic_leakage("```python\ndef sort_list():\n  pass\n```")
