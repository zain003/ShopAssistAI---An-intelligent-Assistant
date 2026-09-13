"""Local LLM Engine & CPU Streaming Adapter using Ollama and HTTPX.

Implements asynchronous streaming inference, readiness probing, warmup routines,
and performance telemetry (TTFT, tokens/sec) per FEAT-001-BE.
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import httpx

from backend.contracts import ErrorPayload, StreamEndPayload
from backend.core.config import (
    DEFAULT_TIMEOUT,
    MODEL_NAME,
    OLLAMA_BASE_URL,
    READY_TIMEOUT,
)


class LLMEngineError(Exception):
    """Exception raised for errors encountered in the LLM Engine."""

    def __init__(
        self,
        message: str = "LLM engine error occurred",
        code: str = "LLM_ENGINE_ERROR",
        recoverable: bool = True,
    ) -> None:
        """Initializes the LLMEngineError.

        Args:
            message: Human-readable error description.
            code: Standardized error code string.
            recoverable: Whether the client or caller can recover from this error.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.recoverable = recoverable

    def to_error_payload(self) -> ErrorPayload:
        """Converts exception to shared contract ErrorPayload.

        Returns:
            ErrorPayload instance.
        """
        return ErrorPayload(
            code=self.code,
            message=self.message,
            recoverable=self.recoverable,
        )


class LLMEngine:
    """Asynchronous client for local CPU-quantized Ollama models."""

    def __init__(
        self,
        host: str = OLLAMA_BASE_URL,
        model: str = MODEL_NAME,
        timeout: float = DEFAULT_TIMEOUT,
        ready_timeout: float = READY_TIMEOUT,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """Initializes the LLM engine adapter.

        Args:
            host: Base URL of the Ollama server.
            model: Model name/identifier.
            timeout: Request timeout in seconds.
            ready_timeout: Readiness probe timeout in seconds.
            client: Optional pre-configured httpx.AsyncClient instance.
        """
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.ready_timeout = ready_timeout
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(base_url=self.host, timeout=self.timeout)

    async def aclose(self) -> None:
        """Closes the underlying HTTP client session if owned."""
        if not self._external_client:
            await self._client.aclose()

    async def __aenter__(self) -> LLMEngine:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Async context manager exit."""
        await self.aclose()

    async def is_ready(self) -> bool:
        """Checks if Ollama service is reachable and target model is available.

        Queries GET /api/tags within the ready_timeout window and verifies that
        the configured model is present in the downloaded models list.

        Returns:
            bool: True if Ollama responds within ready_timeout (2.0s) and model
                is present; False on connection error, timeout, or missing model.
        """
        try:
            response = await self._client.get(
                f"{self.host}/api/tags",
                timeout=self.ready_timeout,
            )
            if response.status_code != 200:
                return False

            data = response.json()
            models = data.get("models", [])
            if not isinstance(models, list):
                return False

            target_model = self.model.lower()
            base_model_name = target_model.split(":")[0]

            for item in models:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).lower()
                model_identifier = str(item.get("model", "")).lower()

                if (
                    name == target_model
                    or model_identifier == target_model
                    or name.startswith(f"{target_model}:")
                    or name.startswith(f"{base_model_name}:")
                    or target_model in name
                ):
                    return True

            return False
        except (httpx.HTTPError, httpx.TimeoutException, Exception):
            return False

    async def warmup(self) -> bool:
        """Pre-warms the local model weights into CPU memory with a 1-token test prompt.

        Returns:
            bool: True if warmup prompt executed successfully.

        Raises:
            LLMEngineError: If Ollama host is unreachable or inference fails.
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False,
            "options": {"num_predict": 1},
        }
        try:
            response = await self._client.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return True
            raise LLMEngineError(
                message=f"Warmup failed with status code {response.status_code}: {response.text}",
                code="INFERENCE_FAILED",
                recoverable=True,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise LLMEngineError(
                message=f"Failed to connect to Ollama at {self.host}: {exc}",
                code="SERVICE_UNAVAILABLE",
                recoverable=True,
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMEngineError(
                message=f"Ollama warmup timed out: {exc}",
                code="INFERENCE_TIMEOUT",
                recoverable=True,
            ) from exc

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        turn_id: str,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> AsyncGenerator[Tuple[str, Optional[StreamEndPayload]], None]:
        """Asynchronously streams response tokens and yields performance telemetry.

        Yields tuples of (token, None) during generation, followed by a final
        tuple of ("", StreamEndPayload) containing TTFT, total tokens, duration,
        and throughput metrics.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            turn_id: Unique turn identifier for telemetry tracking.
            temperature: Sampling temperature between 0.0 and 1.0.
            max_tokens: Maximum tokens to generate.

        Yields:
            Tuple[str, Optional[StreamEndPayload]]: Token chunk followed by final
                telemetry payload.

        Raises:
            LLMEngineError: If Ollama is unreachable, returns HTTP error, or times out.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        t_start = time.perf_counter()
        ttft_ms: Optional[float] = None
        token_count = 0

        try:
            async with self._client.stream(
                "POST",
                f"{self.host}/api/chat",
                json=payload,
                timeout=self.timeout,
            ) as response:
                if response.status_code >= 400:
                    error_bytes = await response.aread()
                    error_text = error_bytes.decode("utf-8", errors="replace")
                    raise LLMEngineError(
                        message=f"Ollama inference failed with status {response.status_code}: {error_text}",
                        code="INFERENCE_FAILED",
                        recoverable=True,
                    )

                async for line in response.aiter_lines():
                    stripped_line = line.strip()
                    if not stripped_line:
                        continue

                    try:
                        chunk = json.loads(stripped_line)
                    except json.JSONDecodeError:
                        continue

                    # Extract delta content from /api/chat or /api/generate format
                    delta = ""
                    message_obj = chunk.get("message")
                    if isinstance(message_obj, dict):
                        delta = str(message_obj.get("content", ""))
                    elif "response" in chunk:
                        delta = str(chunk.get("response", ""))

                    # Filter out empty token chunks
                    if not delta:
                        continue

                    # Compute TTFT on the first non-empty token chunk
                    if ttft_ms is None:
                        t_first = time.perf_counter()
                        ttft_ms = max((t_first - t_start) * 1000.0, 0.01)

                    token_count += 1
                    yield (delta, None)

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise LLMEngineError(
                message=f"Ollama host unreachable at {self.host}: {exc}",
                code="SERVICE_UNAVAILABLE",
                recoverable=True,
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMEngineError(
                message=f"Ollama inference timed out: {exc}",
                code="INFERENCE_TIMEOUT",
                recoverable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMEngineError(
                message=f"HTTP status error: {exc}",
                code="INFERENCE_FAILED",
                recoverable=True,
            ) from exc

        t_end = time.perf_counter()
        total_duration_ms = max((t_end - t_start) * 1000.0, 0.01)
        final_ttft_ms = ttft_ms if ttft_ms is not None else 0.0

        duration_sec = total_duration_ms / 1000.0
        if duration_sec > 0 and token_count > 0:
            tokens_per_second = round(token_count / duration_sec, 2)
        else:
            tokens_per_second = 0.0

        # Guarantee tokens_per_second > 0.0 if token_count > 0
        if token_count > 0 and tokens_per_second <= 0.0:
            tokens_per_second = round(token_count / max(duration_sec, 1e-6), 2)

        end_payload = StreamEndPayload(
            turn_id=turn_id,
            total_tokens=token_count,
            ttft_ms=round(final_ttft_ms, 2),
            total_duration_ms=round(total_duration_ms, 2),
            tokens_per_second=tokens_per_second,
        )

        yield ("", end_payload)
