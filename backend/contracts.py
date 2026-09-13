"""Shared data models, types, and protocol envelopes for ShopAssist AI.

Authoritative source defined in context/feature-specs/000-shared-contracts.md.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    """Message sender role within a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class OrderStatus(str, Enum):
    """Lifecycle status of a customer order."""
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    IN_TRANSIT = "In Transit"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    RETURNED = "Returned"
    CANCELLED = "Cancelled"


class OrderItem(BaseModel):
    """Individual line item within an order."""
    model_config = ConfigDict(frozen=True)

    sku: str
    name: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0.0)


class OrderRecord(BaseModel):
    """Complete customer order entity."""
    model_config = ConfigDict(frozen=True)

    order_id: str  # Format: ORD-XXXX
    customer_name: str
    customer_email: str
    status: OrderStatus
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    order_date: str  # YYYY-MM-DD
    estimated_delivery: Optional[str] = None  # YYYY-MM-DD
    items: List[OrderItem]
    total_amount: float
    shipping_address: str
    return_eligible_until: Optional[str] = None  # YYYY-MM-DD


class CatalogProduct(BaseModel):
    """E-commerce product entity in the store catalog."""
    model_config = ConfigDict(frozen=True)

    sku: str
    name: str
    category: str
    price: float
    in_stock: bool
    stock_count: int
    features: List[str]
    warranty_months: int
    returnable: bool = True


class ChatMessage(BaseModel):
    """A single turn message in a conversation session."""
    model_config = ConfigDict(frozen=True)

    role: Role
    content: str
    timestamp: float


class SessionState(BaseModel):
    """In-memory state and history for an active user session."""
    session_id: str
    created_at: float
    last_active_at: float
    messages: List[ChatMessage] = Field(default_factory=list)
    active_order_id: Optional[str] = None
    active_customer_email: Optional[str] = None
    topic_history: List[str] = Field(default_factory=list)
    total_turns: int = 0


# --- WebSocket Protocol Envelopes ---


class InboundMessageType(str, Enum):
    """Client-to-server WebSocket message types."""
    USER_MESSAGE = "user_message"
    RESET_SESSION = "reset_session"
    PING = "ping"


class UserMessagePayload(BaseModel):
    """Payload for inbound user text message."""
    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1, max_length=2000)


class InboundEnvelope(BaseModel):
    """Wrapper envelope for all inbound client WebSocket messages."""
    model_config = ConfigDict(frozen=True)

    type: InboundMessageType
    session_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class OutboundMessageType(str, Enum):
    """Server-to-client WebSocket message types."""
    SESSION_CREATED = "session_created"
    SESSION_RESET = "session_reset"
    STREAM_START = "stream_start"
    TOKEN = "token"
    STREAM_END = "stream_end"
    ERROR = "error"
    PONG = "pong"


class TokenPayload(BaseModel):
    """Streaming chunk token payload."""
    model_config = ConfigDict(frozen=True)

    token: str
    turn_id: str


class StreamEndPayload(BaseModel):
    """Completion payload emitting performance telemetry."""
    model_config = ConfigDict(frozen=True)

    turn_id: str
    total_tokens: int
    ttft_ms: float           # Time to first token in milliseconds
    total_duration_ms: float # Total response time in milliseconds
    tokens_per_second: float


class ErrorPayload(BaseModel):
    """Structured error payload sent over WebSocket or raised internally."""
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    recoverable: bool = True


class OutboundEnvelope(BaseModel):
    """Wrapper envelope for all outbound server WebSocket messages."""
    model_config = ConfigDict(frozen=True)

    type: OutboundMessageType
    session_id: str
    payload: Dict[str, Any]
