"""Hard out-of-domain deflection gate for ShopAssist AI.

Small local LLMs often partially refuse then still answer coding/trivia.
Any clear off-topic ask skips the LLM entirely — even if the message also
mentions an order ID or other store words.
"""

from __future__ import annotations

import re

STORE_REFUSAL_MESSAGE = (
    "I can only assist with questions regarding our store's products, orders, "
    "returns, and shipping policies."
)

# Signals that the user is asking about ApexStyle / ShopAssist topics
_STORE_TOPIC_PATTERN = re.compile(
    r"\b("
    r"order|orders|ord-\d{4}|tracking|shipment|shipped|shipping|delivery|deliver|"
    r"return|returns|refund|refunds|exchange|cancel|cancellation|"
    r"warranty|warranties|repair|replacement|"
    r"product|products|catalog|sku|price|pricing|stock|in[- ]stock|"
    r"payment|payments|pay|checkout|coupon|promo|gift[- ]?card|"
    r"headphones|earbuds|watch|mouse|keyboard|backpack|charger|powerbank|"
    r"projector|tablet|bluetooth|firmware|battery|pairing|factory[- ]?reset|"
    r"soundflow|pulse|aerogrip|titanshield|echobeam|swiftcharge|novatab|"
    r"apexstyle|shopassist|store|policy|policies|"
    r"total|subtotal|tax|discount|fee|fees|crm|remember|preference|preferences|my name"
    r")\b",
    re.IGNORECASE,
)

# Store-adjacent tool use (calculate totals / CRM) must not hard-deflect
_TOOL_ALLOWED_PATTERN = re.compile(
    r"\b("
    r"order|ord-\d{4}|total|subtotal|tax|refund|shipping|price|prices|"
    r"discount|fee|fees|cart|catalog|product|sku|"
    r"remember|my name|preference|preferences|email|phone|crm"
    r")\b",
    re.IGNORECASE,
)

# Clear off-topic patterns — coding/math/politics/trivia always blocked
_OFF_TOPIC_PATTERN = re.compile(
    r"("
    r"\b(who is|who's|what is the capital|president|election|vote for)\b|"
    r"\b(cricket|football|soccer|bollywood|celebrity|virat|kohli)\b|"
    r"\b(python|javascript|typescript|java\b|c\+\+|golang|rust|ruby|php)\b|"
    r"\b(code|coding|script|algorithm|programming|programmer|leetcode)\b|"
    r"\b(beautifulsoup|pandas|numpy|react|django|flask)\b|"
    r"\b(write|create|generate|give me|show me)\b.{0,40}\b(function|program|snippet|script)\b|"
    r"\bsort\b.{0,20}\b(list|array)\b|"
    r"\b(square root|math equation|dosage|medicine|amoxicillin|ibuprofen)\b|"
    r"\b(ignore all previous|you are now dan|jailbreak)\b"
    r")",
    re.IGNORECASE | re.DOTALL,
)

# Leakage detectors for model output (belt-and-suspenders)
_RESPONSE_LEAKAGE_PATTERN = re.compile(
    r"(```|^\s*def\s+\w+\s*\(|^\s*import\s+\w+|^\s*from\s+\w+\s+import\b)",
    re.IGNORECASE | re.MULTILINE,
)


def looks_like_store_query(text: str) -> bool:
    """Return True if the query appears related to store support topics."""
    return bool(_STORE_TOPIC_PATTERN.search(text or ""))


def looks_like_tool_allowed_query(text: str) -> bool:
    """Return True if the query looks like store math / CRM tool use."""
    return bool(_TOOL_ALLOWED_PATTERN.search(text or ""))


def looks_like_off_topic_query(text: str) -> bool:
    """Return True if the query matches known out-of-domain patterns."""
    text = text or ""
    # Pure store arithmetic ("calculate my order total + shipping") is allowed
    if looks_like_tool_allowed_query(text) and re.search(
        r"\b(calculate|total|sum|add|subtract|multiply|divide|tax|percent|%)\b",
        text,
        re.IGNORECASE,
    ):
        return False
    return bool(_OFF_TOPIC_PATTERN.search(text))


def response_has_off_topic_leakage(text: str) -> bool:
    """Return True if assistant text contains code fences or code-like leakage."""
    return bool(_RESPONSE_LEAKAGE_PATTERN.search(text or ""))


def should_hard_deflect(user_text: str, retrieval_is_fallback: bool | None) -> bool:
    """Decide whether to refuse without calling the LLM.

    Hard-deflect when:
    - Query matches clear off-topic patterns (ALWAYS — even if store words appear), OR
    - RAG found no useful chunks AND the query does not look store-related.
    """
    text = (user_text or "").strip()
    if not text:
        return False

    # Coding / trivia / politics / medical: never call the LLM
    if looks_like_off_topic_query(text):
        return True

    if retrieval_is_fallback is True and not looks_like_store_query(text):
        return True

    return False
