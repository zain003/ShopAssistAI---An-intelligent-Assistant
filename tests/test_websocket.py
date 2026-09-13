"""Integration tests for FastAPI WebSocket API and REST endpoints.

Tests health check, WebSocket lifecycle, token streaming, error recovery,
session reset, concurrency, and graceful disconnects per FEAT-003-BE and FEAT-003-VERIFY.
"""

from __future__ import annotations

import concurrent.futures
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
import uuid

from fastapi.testclient import TestClient
import pytest

from backend.api.main import create_app
from backend.contracts import StreamEndPayload
from backend.conversation.manager import ConversationManager
from backend.core.llm import LLMEngine, LLMEngineError


class MockLLMEngine(LLMEngine):
    """Controllable mock for LLMEngine in integration tests."""

    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        should_fail: bool = False,
        fail_code: str = "INFERENCE_TIMEOUT",
        tokens: Optional[List[str]] = None,
        is_ready_state: bool = True,
    ) -> None:
        """Initializes the mock LLM engine.

        Args:
            model: Model identifier string.
            should_fail: If True, raises an error during stream generation.
            fail_code: Error code to raise if should_fail is True.
            tokens: Sequence of tokens to emit.
            is_ready_state: Boolean returned by is_ready().
        """
        self.model = model
        self.should_fail = should_fail
        self.fail_code = fail_code
        self.tokens = tokens or ["Hello", " customer", "! ", "How", " can", " I", " help?"]
        self.is_ready_state = is_ready_state
        self.warmup_called = False
        self.closed = False

    async def is_ready(self) -> bool:
        """Returns mock readiness state."""
        return self.is_ready_state

    async def warmup(self) -> bool:
        """Simulates engine warmup."""
        self.warmup_called = True
        return True

    async def aclose(self) -> None:
        """Simulates resource closure."""
        self.closed = True

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        turn_id: str,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> AsyncGenerator[Tuple[str, Optional[StreamEndPayload]], None]:
        """Yields mock tokens followed by telemetry completion payload."""
        if self.should_fail:
            raise LLMEngineError(
                message="Mock inference failure occurred",
                code=self.fail_code,
                recoverable=True,
            )

        for token in self.tokens:
            yield (token, None)

        yield (
            "",
            StreamEndPayload(
                turn_id=turn_id,
                total_tokens=len(self.tokens),
                ttft_ms=45.2,
                total_duration_ms=120.5,
                tokens_per_second=58.1,
            ),
        )


@pytest.fixture
def mock_engine() -> MockLLMEngine:
    """Fixture providing a fresh mock LLMEngine."""
    return MockLLMEngine()


@pytest.fixture
def conv_manager() -> ConversationManager:
    """Fixture providing an in-memory ConversationManager."""
    return ConversationManager()


@pytest.fixture
def app(mock_engine: MockLLMEngine, conv_manager: ConversationManager):
    """Fixture providing configured FastAPI application instance."""
    return create_app(llm_engine=mock_engine, conversation_manager=conv_manager)


@pytest.fixture
def client(app) -> TestClient:
    """Fixture providing FastAPI TestClient."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Core Feature Verification Tests
# ---------------------------------------------------------------------------


def test_health_endpoint_returns_ok(client: TestClient, mock_engine: MockLLMEngine) -> None:
    """GET /api/health returns HTTP 200 with status='ok', model, and ready flag."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == mock_engine.model
    assert data["ready"] is True


def test_ws_connection_emits_session_created(client: TestClient) -> None:
    """Connecting to /ws/chat immediately emits session_created with a valid UUID."""
    with client.websocket_connect("/ws/chat") as ws:
        frame = ws.receive_json()
        assert frame["type"] == "session_created"
        session_id = frame["session_id"]
        # Validate that session_id is a valid UUID
        parsed_uuid = uuid.UUID(session_id)
        assert str(parsed_uuid) == session_id
        assert frame["payload"]["session_id"] == session_id


def test_ws_user_message_streams_tokens_and_end(
    client: TestClient,
    conv_manager: ConversationManager,
    mock_engine: MockLLMEngine,
) -> None:
    """Sending user_message streams stream_start, tokens, and stream_end."""
    with client.websocket_connect("/ws/chat") as ws:
        # 1. Receive session_created
        init_frame = ws.receive_json()
        session_id = init_frame["session_id"]

        # 2. Dispatch user_message
        ws.send_json({
            "type": "user_message",
            "payload": {"text": "Where is my order ORD-1002?"},
        })

        # 3. Receive stream_start
        start_frame = ws.receive_json()
        assert start_frame["type"] == "stream_start"
        assert start_frame["session_id"] == session_id
        turn_id = start_frame["payload"]["turn_id"]
        assert turn_id.startswith("turn_")

        # 4. Receive token frames
        received_tokens = []
        for _ in range(len(mock_engine.tokens)):
            token_frame = ws.receive_json()
            assert token_frame["type"] == "token"
            assert token_frame["session_id"] == session_id
            assert token_frame["payload"]["turn_id"] == turn_id
            received_tokens.append(token_frame["payload"]["token"])

        assert received_tokens == mock_engine.tokens

        # 5. Receive stream_end frame
        end_frame = ws.receive_json()
        assert end_frame["type"] == "stream_end"
        assert end_frame["session_id"] == session_id
        payload = end_frame["payload"]
        assert payload["turn_id"] == turn_id
        assert payload["total_tokens"] == len(mock_engine.tokens)
        assert payload["ttft_ms"] > 0
        assert payload["tokens_per_second"] > 0

        # Verify messages and entities were saved in ConversationManager
        session_state = conv_manager.get_or_create_session(session_id)
        assert len(session_state.messages) == 2
        assert session_state.messages[0].role.value == "user"
        assert session_state.messages[0].content == "Where is my order ORD-1002?"
        assert session_state.messages[1].role.value == "assistant"
        assert session_state.messages[1].content == "".join(mock_engine.tokens)
        assert session_state.active_order_id == "ORD-1002"


def test_ws_malformed_json_emits_error_frame(client: TestClient) -> None:
    """Invalid JSON emits INVALID_PAYLOAD error without severing the connection."""
    with client.websocket_connect("/ws/chat") as ws:
        init_frame = ws.receive_json()
        session_id = init_frame["session_id"]

        # Send malformed JSON string
        ws.send_text('{"bad json: [unclosed')

        error_frame = ws.receive_json()
        assert error_frame["type"] == "error"
        assert error_frame["session_id"] == session_id
        assert error_frame["payload"]["code"] == "INVALID_PAYLOAD"
        assert error_frame["payload"]["recoverable"] is True

        # Ensure the socket remains open and responsive to subsequent valid frames
        ws.send_json({"type": "ping"})
        pong_frame = ws.receive_json()
        assert pong_frame["type"] == "pong"
        assert pong_frame["session_id"] == session_id


def test_ws_reset_session_emits_session_reset(
    client: TestClient,
    conv_manager: ConversationManager,
) -> None:
    """Sending reset_session zeroes history and emits session_reset."""
    with client.websocket_connect("/ws/chat") as ws:
        init_frame = ws.receive_json()
        session_id = init_frame["session_id"]

        # Add a message first
        ws.send_json({
            "type": "user_message",
            "payload": {"text": "I ordered ORD-1085"},
        })
        # Discard stream frames
        ws.receive_json()  # stream_start
        while True:
            frame = ws.receive_json()
            if frame["type"] == "stream_end":
                break

        # Verify state exists
        session = conv_manager.get_or_create_session(session_id)
        assert len(session.messages) > 0
        assert session.active_order_id == "ORD-1085"

        # Now send reset_session
        ws.send_json({"type": "reset_session"})
        reset_frame = ws.receive_json()
        assert reset_frame["type"] == "session_reset"
        assert reset_frame["session_id"] == session_id
        assert reset_frame["payload"]["status"] == "reset"

        # Verify state cleared
        session_after = conv_manager.get_or_create_session(session_id)
        assert len(session_after.messages) == 0
        assert session_after.active_order_id is None
        assert session_after.total_turns == 0


# ---------------------------------------------------------------------------
# Edge Cases & Robustness Tests
# ---------------------------------------------------------------------------


def test_ws_empty_message_emits_error(client: TestClient) -> None:
    """Empty or whitespace-only user message emits EMPTY_MESSAGE and socket stays open."""
    with client.websocket_connect("/ws/chat") as ws:
        ws.receive_json()  # session_created

        # Send empty string
        ws.send_json({"type": "user_message", "payload": {"text": "   "}})
        error_frame = ws.receive_json()
        assert error_frame["type"] == "error"
        assert error_frame["payload"]["code"] == "EMPTY_MESSAGE"
        assert error_frame["payload"]["recoverable"] is True

        # Send missing text field
        ws.send_json({"type": "user_message", "payload": {}})
        error_frame2 = ws.receive_json()
        assert error_frame2["type"] == "error"
        assert error_frame2["payload"]["code"] == "EMPTY_MESSAGE"

        # Verify connection stays open
        ws.send_json({"type": "ping"})
        pong_frame = ws.receive_json()
        assert pong_frame["type"] == "pong"


def test_ws_invalid_envelope_type_emits_error(client: TestClient) -> None:
    """Sending unknown or invalid envelope type emits INVALID_PAYLOAD error."""
    with client.websocket_connect("/ws/chat") as ws:
        ws.receive_json()  # session_created

        ws.send_json({"type": "unknown_action_foo", "payload": {}})
        error_frame = ws.receive_json()
        assert error_frame["type"] == "error"
        assert error_frame["payload"]["code"] == "INVALID_PAYLOAD"


def test_ws_ping_pong(client: TestClient) -> None:
    """Sending ping returns pong envelope with timestamp."""
    with client.websocket_connect("/ws/chat") as ws:
        init_frame = ws.receive_json()
        session_id = init_frame["session_id"]

        ws.send_json({"type": "ping"})
        pong_frame = ws.receive_json()
        assert pong_frame["type"] == "pong"
        assert pong_frame["session_id"] == session_id
        assert "timestamp" in pong_frame["payload"]


def test_ws_custom_session_id_query_param(client: TestClient) -> None:
    """Passing custom session_id in query string uses that session_id."""
    custom_id = "custom-session-uuid-999"
    with client.websocket_connect(f"/ws/chat?session_id={custom_id}") as ws:
        init_frame = ws.receive_json()
        assert init_frame["session_id"] == custom_id
        assert init_frame["payload"]["session_id"] == custom_id


def test_ws_inference_error_emits_error_frame(
    conv_manager: ConversationManager,
) -> None:
    """Inference failure during streaming emits error frame and preserves socket."""
    failing_engine = MockLLMEngine(should_fail=True, fail_code="INFERENCE_FAILED")
    app = create_app(llm_engine=failing_engine, conversation_manager=conv_manager)
    client = TestClient(app)

    with client.websocket_connect("/ws/chat") as ws:
        ws.receive_json()  # session_created

        ws.send_json({"type": "user_message", "payload": {"text": "Cause inference error"}})
        ws.receive_json()  # stream_start

        error_frame = ws.receive_json()
        assert error_frame["type"] == "error"
        assert error_frame["payload"]["code"] == "INFERENCE_FAILED"
        assert error_frame["payload"]["recoverable"] is True

        # Verify connection stays open
        ws.send_json({"type": "ping"})
        pong_frame = ws.receive_json()
        assert pong_frame["type"] == "pong"


def test_ws_client_disconnect_mid_stream(
    client: TestClient,
    mock_engine: MockLLMEngine,
) -> None:
    """Client disconnecting mid-stream terminates cleanly without server crash."""
    with client.websocket_connect("/ws/chat") as ws:
        ws.receive_json()  # session_created
        ws.send_json({"type": "user_message", "payload": {"text": "Disconnect test"}})
        ws.receive_json()  # stream_start
        ws.receive_json()  # 1st token
        # Client closes mid-stream
        ws.close()

    # Verify a subsequent connection operates normally
    with client.websocket_connect("/ws/chat") as ws2:
        frame = ws2.receive_json()
        assert frame["type"] == "session_created"


def test_ws_concurrent_connections(app) -> None:
    """AC-5: 5 concurrent connections stream responses without cross-talk or blocking."""
    client = TestClient(app)

    def run_session(index: int) -> Dict[str, Any]:
        session_id = f"concurrent-session-{index}"
        frames: List[Dict[str, Any]] = []
        with client.websocket_connect(f"/ws/chat?session_id={session_id}") as ws:
            # 1. session_created
            created = ws.receive_json()
            frames.append(created)

            # 2. send message
            ws.send_json({
                "type": "user_message",
                "payload": {"text": f"Question from connection {index}"},
            })

            # 3. read until stream_end
            while True:
                msg = ws.receive_json()
                frames.append(msg)
                if msg.get("type") == "stream_end":
                    break

        return {"index": index, "session_id": session_id, "frames": frames}

    # Run 5 concurrent sessions simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_session, i) for i in range(5)]
        results = [f.result(timeout=10.0) for f in futures]

    assert len(results) == 5
    for res in results:
        idx = res["index"]
        expected_sid = f"concurrent-session-{idx}"
        frames = res["frames"]

        # Ensure frames belong exclusively to this session
        for f in frames:
            assert f["session_id"] == expected_sid

        # Check expected sequence: session_created, stream_start, tokens, stream_end
        types = [f["type"] for f in frames]
        assert types[0] == "session_created"
        assert types[1] == "stream_start"
        assert types[-1] == "stream_end"
        assert "token" in types


def test_server_startup_warmup_lifespan() -> None:
    """Lifespan event completes with zero exceptions during startup and shutdown."""
    ready_engine = MockLLMEngine(is_ready_state=True)
    ready_app = create_app(llm_engine=ready_engine)

    with TestClient(ready_app):
        assert ready_engine.warmup_called is True

    assert ready_engine.closed is True

    # Test with engine not ready at startup
    unready_engine = MockLLMEngine(is_ready_state=False)
    unready_app = create_app(llm_engine=unready_engine)

    with TestClient(unready_app):
        assert unready_engine.warmup_called is False

    assert unready_engine.closed is True
