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

### 1.2 Retrieval-Augmented Generation (RAG) Schemas (Assignment 2)

```python
class DocumentMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    doc_id: str
    title: str
    category: str  # e.g., "policy", "product_faq", "shipping", "warranty", "troubleshooting"
    source_path: str
    doc_hash: str
    created_at: float

class DocumentChunk(BaseModel):
    model_config = ConfigDict(frozen=True)
    chunk_id: str
    doc_id: str
    title: str
    section_header: str
    content: str
    token_count: int
    char_count: int
    chunk_index: int
    embedding: Optional[List[float]] = None  # None when serialized to client

class RetrievalQuery(BaseModel):
    model_config = ConfigDict(frozen=True)
    query_text: str
    top_k: int = Field(default=3, ge=1, le=10)
    score_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    category_filter: Optional[str] = None

class CitationItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    doc_id: str
    title: str
    section_header: str
    score: float
    snippet: str

class RetrievalResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    query: str
    chunks: List[DocumentChunk]
    citations: List[CitationItem]
    retrieval_ms: float
    from_cache: bool = False
    is_fallback: bool = False  # True when no chunks exceed score_threshold

class RetrievalMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    total_retrieval_ms: float
    chunks_evaluated: int
    chunks_returned: int
    cache_hit: bool
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
    ttft_ms: float                     # Time to first token in milliseconds
    total_duration_ms: float           # Total response time in milliseconds
    tokens_per_second: float
    retrieval_ms: Optional[float] = None  # Retrieval latency in milliseconds (RAG)
    citations: List[CitationItem] = Field(default_factory=list)  # Grounded document citations

class ErrorPayload(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str  # E.g. "INVALID_PAYLOAD", "INFERENCE_TIMEOUT", "RETRIEVAL_TIMEOUT", "NO_RELEVANT_DOCS"
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

export interface CitationItem {
  doc_id: string;
  title: string;
  section_header: string;
  score: number;
  snippet: string;
}

export interface StreamEndMetrics {
  turn_id: string;
  total_tokens: number;
  ttft_ms: number;
  total_duration_ms: number;
  tokens_per_second: number;
  retrieval_ms?: number;
  citations?: CitationItem[];
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
2. **Context Window Token Budget (RAG Enhanced)**:
   - Total Model Context: 2,048 tokens (or 4,096 tokens).
   - System Persona & Guardrails: ~450 tokens.
   - Dynamic Dialogue History: Last 6 turns (12 messages) = ~600 tokens max.
   - Retrieved Context Injection (`<retrieved_context>`): Top-3 chunks = ~500 tokens max.
   - Active Session Order / State: ~100 tokens.
   - Generation Output Reserve: 398 tokens.
   - Hard Rule: If History + Retrieved Context exceeds 1,500 tokens, the Conversation Manager must prune oldest history messages before dropping retrieved knowledge chunks.
3. **Standard Error Codes**:
   - `INVALID_PAYLOAD`: Malformed or unparseable client WebSocket JSON.
   - `INFERENCE_TIMEOUT`: Ollama token generation stream stalled > 60s.
   - `RETRIEVAL_TIMEOUT`: Vector search / embedding generation took > 1.0s.
   - `INDEX_NOT_FOUND`: Document vector store uninitialized or unavailable.
   - `NO_RELEVANT_DOCS`: Similarity search returned 0 chunks above threshold (triggers fallback).
   - `SESSION_NOT_FOUND`: Referenced session expired or missing.
4. **Naming Conventions**:
   - Python files: `snake_case.py`
   - Python classes: `PascalCase`
   - Python functions/methods: `snake_case`
   - Frontend files: `kebab-case.js`, `style.css`
   - WebSocket event types: `snake_case` string constants
5. **Mock Order ID Standard**:
   - All mock orders must follow regex `^ORD-\d{4}$` (e.g. `ORD-1001`, `ORD-1002`, `ORD-1085`).

