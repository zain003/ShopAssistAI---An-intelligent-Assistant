# Code Standards

## General Principles

- **Single Responsibility**: Every module, class, and service function must own exactly one responsibility (e.g. LLM streaming separate from prompt orchestration).
- **Explicit Error Handling**: Never catch generic `Exception` silently; log errors with context and return structured error payloads over WebSocket.
- **Async-First**: All network operations, LLM streaming, and WebSocket communications must use native Python `async`/`await`.
- **Zero Hallucination / Zero Speculation**: Adhere strictly to the specs and data structures defined in `context/feature-specs/000-shared-contracts.md`.

---

## Python 3.11+ Standards

- **Type Annotations**: Mandatory type hints on all function parameters, return values, and class attributes. Run with strict `mypy` check.
- **Pydantic v2**: Use `pydantic.BaseModel` with `ConfigDict(frozen=True)` or validated types for all domain models and WebSocket message schemas.
- **Docstrings & Comments**: Every public function and class must have concise Google-style docstrings detailing inputs, returns, and raised exceptions.
- **Constants**: Static data (mock orders, catalog, prompt templates) must be defined in uppercase constants within dedicated configuration modules.

```python
# Standard function signature example
async def stream_chat_response(
    session_id: str,
    user_prompt: str,
) -> AsyncGenerator[StreamChunk, None]:
    """Streams token chunks from local LLM for a given user session.
    
    Args:
        session_id: Unique session identifier string.
        user_prompt: Sanitized text message from user.
        
    Yields:
        StreamChunk instances containing token text and metadata.
    """
```

---

## WebSocket & Protocol Standards

- **Envelope Contract**: Every WebSocket frame must be a valid JSON string conforming to the schemas in `000-shared-contracts.md`.
- **Message Types**:
  - Inbound: `user_message`, `session_reset`, `ping`
  - Outbound: `session_created`, `stream_start`, `token`, `stream_end`, `error`, `pong`
- **Graceful Error Recovery**: If an invalid JSON payload is received, the server returns an `error` frame with code `INVALID_PAYLOAD` without closing the connection.
- **Streaming Granularity**: Tokens must be pushed to the client immediately as they arrive from the LLM engine (`flush=True` behavior).

---

## Prompt Engineering & Memory Standards

- **XML Delimiters**: System prompts must enclose reference data in XML tags (`<persona>`, `<store_catalog>`, `<order_records>`, `<store_policies>`, `<conversation_rules>`). This structure helps small quantized models adhere to instructions.
- **Deflection Guard**: The system prompt must explicitly instruct the model: *"If the user asks about anything outside of this store's products, orders, returns, or shipping, respond: 'I can only assist with questions regarding our store's products, orders, returns, and shipping policies.'"*
- **Sliding-Window Truncation**: Memory manager must compute approximate token counts and keep only the latest $N$ turns (default 6 turns / 12 messages) plus the persistent system prompt.

---

## Frontend Standards

- **Semantic CSS**: All styles must consume CSS custom properties defined in `context/ui-context.md`. No hardcoded hex color values or random font sizes.
- **Resilient WebSocket Client**: The frontend must manage connection state (`connecting`, `connected`, `streaming`, `disconnected`), display clear visual badges, and support automatic reconnection.
- **Accessibility**: Use semantic HTML (`<main>`, `<section>`, `<button>`, `<input>`) with appropriate ARIA roles (`role="log"`, `aria-live="polite"` on message list).

---

## File Organization

```
nlp-assignment-01/
├── backend/
│   ├── api/                 # FastAPI app, REST routers, WebSocket endpoint
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── routes.py        # REST endpoints (/api/health, /api/benchmarks)
│   │   └── websocket.py     # WebSocket endpoint (/ws/chat)
│   ├── core/                # LLM engine and inference client
│   │   ├── __init__.py
│   │   ├── config.py        # System settings and environment variables
│   │   └── llm.py           # Ollama/llama.cpp async streaming client
│   └── conversation/        # Session, prompt, and memory orchestration
│       ├── __init__.py
│       ├── data.py          # Static mock orders, catalog, and store policies
│       ├── memory.py        # Sliding-window context management
│       ├── orchestrator.py  # Structured system prompt builder
│       └── manager.py       # Session lifecycle and turn tracker
├── frontend/
│   ├── index.html           # Single-page web chat application
│   ├── style.css            # Modern CSS styling with design tokens
│   └── app.js               # WebSocket client & DOM streaming renderer
├── tests/
│   ├── test_llm_engine.py   # LLM streaming & fallback unit tests
│   ├── test_conversation.py # Memory pruning & prompt builder unit tests
│   ├── test_websocket.py    # WebSocket API contract & concurrency tests
│   └── test_frontend.js     # DOM rendering & event simulation tests
├── context/                 # Core project context files
│   ├── feature-specs/       # Spec-driven feature definitions
│   └── ...
├── feature-test-reports/    # SQA verification reports
├── README.md                # Setup, benchmarks, architecture documentation
└── requirements.txt         # Python dependencies
```
