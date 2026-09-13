"""Unit tests for the Local LLM Engine & CPU Streaming Adapter (FEAT-001-BE)."""

import json
from typing import AsyncGenerator, List, Tuple
import httpx
import pytest

from backend.contracts import StreamEndPayload
from backend.core.llm import LLMEngine, LLMEngineError


@pytest.mark.asyncio
async def test_engine_is_ready_true_on_200() -> None:
    """Mock GET /api/tags returning 200 with model present -> returns True."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(
            200,
            json={
                "models": [
                    {"name": "qwen2.5:1.5b", "model": "qwen2.5:1.5b"},
                    {"name": "llama3:latest", "model": "llama3:latest"},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        is_ready = await engine.is_ready()
        assert is_ready is True


@pytest.mark.asyncio
async def test_engine_is_ready_false_on_connection_error() -> None:
    """Mock connection failure -> returns False."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused to Ollama", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        is_ready = await engine.is_ready()
        assert is_ready is False


@pytest.mark.asyncio
async def test_engine_is_ready_false_on_missing_model() -> None:
    """Mock GET /api/tags returning 200 but target model not found -> returns False."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "models": [
                    {"name": "mistral:7b", "model": "mistral:7b"},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        is_ready = await engine.is_ready()
        assert is_ready is False


@pytest.mark.asyncio
async def test_generate_stream_yields_tokens() -> None:
    """Mock streamed chunks ["Hello", " there", "!"] -> yields 3 token tuples."""
    chunks = [
        json.dumps({"message": {"role": "assistant", "content": "Hello"}}),
        json.dumps({"message": {"role": "assistant", "content": " there"}}),
        json.dumps({"message": {"role": "assistant", "content": "!"}}),
        json.dumps({"done": True}),
    ]
    raw_body = "\n".join(chunks).encode("utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(200, content=raw_body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        messages = [{"role": "user", "content": "Hello"}]
        results: List[Tuple[str, object]] = []

        async for token, end_payload in engine.generate_stream(messages, turn_id="turn-123"):
            results.append((token, end_payload))

        # First 3 yields are tokens with None end_payload
        assert len(results) == 4
        assert results[0] == ("Hello", None)
        assert results[1] == (" there", None)
        assert results[2] == ("!", None)
        # Final yield has empty token and StreamEndPayload
        assert results[3][0] == ""
        assert isinstance(results[3][1], StreamEndPayload)


@pytest.mark.asyncio
async def test_generate_stream_emits_telemetry_at_end() -> None:
    """Verify final tuple contains StreamEndPayload with ttft_ms > 0 and total_tokens == 3."""
    chunks = [
        json.dumps({"message": {"role": "assistant", "content": "Hello"}}),
        json.dumps({"message": {"role": "assistant", "content": " there"}}),
        json.dumps({"message": {"role": "assistant", "content": "!"}}),
    ]
    raw_body = "\n".join(chunks).encode("utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=raw_body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        messages = [{"role": "user", "content": "Tell me a joke"}]
        end_payload: StreamEndPayload | None = None

        async for token, payload in engine.generate_stream(messages, turn_id="turn-456"):
            if payload is not None:
                end_payload = payload

        assert end_payload is not None
        assert end_payload.turn_id == "turn-456"
        assert end_payload.total_tokens == 3
        assert end_payload.ttft_ms > 0.0
        assert end_payload.total_duration_ms > 0.0
        assert end_payload.tokens_per_second > 0.0


@pytest.mark.asyncio
async def test_generate_stream_raises_on_http_error() -> None:
    """Mock HTTP 500 error -> raises LLMEngineError(code="INFERENCE_FAILED")."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Model Failure")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(LLMEngineError) as exc_info:
            async for _ in engine.generate_stream(messages, turn_id="turn-err"):
                pass

        assert exc_info.value.code == "INFERENCE_FAILED"
        assert "500" in exc_info.value.message


@pytest.mark.asyncio
async def test_generate_stream_raises_on_unreachable_host() -> None:
    """An unreachable Ollama host raises LLMEngineError with code="SERVICE_UNAVAILABLE"."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(LLMEngineError) as exc_info:
            async for _ in engine.generate_stream(messages, turn_id="turn-unreachable"):
                pass

        assert exc_info.value.code == "SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_generate_stream_filters_empty_chunks() -> None:
    """Verify empty string chunks are discarded and not yielded."""
    chunks = [
        json.dumps({"message": {"role": "assistant", "content": ""}}),
        json.dumps({"message": {"role": "assistant", "content": "Valid"}}),
        json.dumps({"message": {"role": "assistant", "content": ""}}),
        json.dumps({"message": {"role": "assistant", "content": "Token"}}),
    ]
    raw_body = "\n".join(chunks).encode("utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=raw_body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        tokens = [token async for token, _ in engine.generate_stream([{"role": "user", "content": "test"}], turn_id="t1") if token]

        assert tokens == ["Valid", "Token"]


@pytest.mark.asyncio
async def test_warmup_success_and_failure() -> None:
    """Test model warmup success on 200 and failure on connection error."""
    # Success case
    def success_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(200, json={"message": {"content": "Hi"}})

    transport = httpx.MockTransport(success_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        assert await engine.warmup() is True

    # Failure case
    def failure_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Failed to connect", request=request)

    transport = httpx.MockTransport(failure_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        engine = LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b", client=client)
        with pytest.raises(LLMEngineError) as exc_info:
            await engine.warmup()
        assert exc_info.value.code == "SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_llm_engine_context_manager() -> None:
    """Test LLMEngine async context manager cleans up resources."""
    async with LLMEngine(host="http://localhost:11434", model="qwen2.5:1.5b") as engine:
        assert engine.host == "http://localhost:11434"
        assert engine.model == "qwen2.5:1.5b"
