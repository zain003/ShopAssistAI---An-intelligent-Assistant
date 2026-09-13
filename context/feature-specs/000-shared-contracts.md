# 000-shared-contracts.md — Single Source of Truth

This file is the authoritative contract for data structures, schemas, WebSocket envelopes, error shapes, and system conventions across the ShopAssist AI project. Every feature specification references these types directly.

---

## 1. Global Core Types & Schemas

### 1.1 Python Core Domain Schemas (Pydantic v2)

```python
from __future__ import annotations
from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class OrderStatus(str, Enum):
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    IN_TRANSIT = "In Transit"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    RETURNED = "Returned"
    CANCELLED = "Cancelled"

class OrderItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    sku: str
    name: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0.0)

class OrderRecord(BaseModel):
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
    model_config = ConfigDict(frozen=True)
    role: Role
    content: str
    timestamp: float

class SessionState(BaseModel):
    session_id: str
    created_at: float
    last_active_at: float
    messages: List[ChatMessage] = Field(default_factory=list)
    active_order_id: Optional[str] = None
    active_customer_email: Optional[str] = None
    topic_history: List[str] = Field(default_factory=list)
    total_turns: int = 0
```

---

## 2. WebSocket Protocol Envelopes

### 2.1 Inbound Messages (Client -> Server)

```python
class InboundMessageType(str, Enum):
    USER_MESSAGE = "user_message"
    RESET_SESSION = "reset_session"
    PING = "ping"

class UserMessagePayload(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str = Field(min_length=1, max_length=2000)

class InboundEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: InboundMessageType
    session_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
```

### 2.2 Outbound Messages (Server -> Client)

```python
class OutboundMessageType(str, Enum):
    SESSION_CREATED = "session_created"
    SESSION_RESET = "session_reset"
    STREAM_START = "stream_start"
    TOKEN = "token"
    STREAM_END = "stream_end"
    ERROR = "error"
    PONG = "pong"

class TokenPayload(BaseModel):
    model_config = ConfigDict(frozen=True)
    token: str
    turn_id: str

class StreamEndPayload(BaseModel):
    model_config = ConfigDict(frozen=True)
    turn_id: str
    total_tokens: int
    ttft_ms: float           # Time to first token in milliseconds
    total_duration_ms: float # Total response time in milliseconds
    tokens_per_second: float

class ErrorPayload(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str  # E.g. "INVALID_PAYLOAD", "INFERENCE_TIMEOUT", "SESSION_NOT_FOUND"
    message: str
    recoverable: bool = True

class OutboundEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: OutboundMessageType
    session_id: str
    payload: Dict[str, Any]
```

---

## 3. TypeScript Client-Side Contracts

```typescript
export type InboundMessageType = "user_message" | "reset_session" | "ping";

export type OutboundMessageType =
  | "session_created"
  | "session_reset"
  | "stream_start"
  | "token"
  | "stream_end"
  | "error"
  | "pong";

export interface OutboundMessage {
  type: OutboundMessageType;
  session_id: string;
  payload: Record<string, any>;
}

export interface StreamEndMetrics {
  turn_id: string;
  total_tokens: number;
  ttft_ms: number;
  total_duration_ms: number;
  tokens_per_second: number;
}

export interface ErrorDetails {
  code: string;
  message: string;
  recoverable: boolean;
}
```

---

## 4. Cross-Cutting Conventions & Rules

1. **Error Response Shape**: Any runtime failure within a WebSocket stream emits:
   ```json
   {
     "type": "error",
     "session_id": "<UUID4>",
     "payload": {
       "code": "<STANDARD_CODE>",
       "message": "<Human-readable description>",
       "recoverable": true
     }
   }
   ```
2. **Context Window Token Budget**:
   - Total Budget: 2,048 tokens.
   - System Prompt (Persona + Catalog + Orders + Policies): ~600 tokens.
   - Dynamic History Window: Last 6 turns (12 messages) = ~800 tokens max.
   - Generation Output Reserve: 512 tokens.
3. **Naming Conventions**:
   - Python files: `snake_case.py`
   - Python classes: `PascalCase`
   - Python functions/methods: `snake_case`
   - Frontend files: `kebab-case.js`, `style.css`
   - WebSocket event types: `snake_case` string constants
4. **Mock Order ID Standard**:
   - All mock orders must follow regex `^ORD-\d{4}$` (e.g. `ORD-1001`, `ORD-1002`, `ORD-1085`).
