"""FastAPI WebSocket chat streaming endpoint for ShopAssist AI.

Implements bidirectional JSON envelope protocol, token-by-token streaming,
session state coordination, and non-fatal error recovery per FEAT-003-BE.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.contracts import (
    ErrorPayload,
    InboundEnvelope,
    InboundMessageType,
    OutboundEnvelope,
    OutboundMessageType,
)
from backend.conversation.manager import ConversationManager
from backend.core.llm import LLMEngine, LLMEngineError

logger = logging.getLogger("backend.api.websocket")

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket) -> None:
    """Asynchronous WebSocket endpoint for real-time chat streaming.

    Accepts client connections, negotiates or initializes session state,
    streams LLM output tokens in real-time, and isolates errors.

    Args:
        websocket: Active FastAPI WebSocket connection.
    """
    await websocket.accept()

    conversation_manager: ConversationManager = (
        getattr(websocket.app.state, "conversation_manager", None)
        or ConversationManager()
    )
    llm_engine: LLMEngine = (
        getattr(websocket.app.state, "llm_engine", None)
        or LLMEngine()
    )

    # Initialize or resume session
    query_session_id = websocket.query_params.get("session_id")
    initial_session_id = (
        query_session_id.strip()
        if (query_session_id and query_session_id.strip())
        else str(uuid.uuid4())
    )
    session = conversation_manager.get_or_create_session(initial_session_id)
    current_session_id = session.session_id

    # Emit initial session_created envelope
    created_envelope = OutboundEnvelope(
        type=OutboundMessageType.SESSION_CREATED,
        session_id=current_session_id,
        payload={"session_id": current_session_id},
    )
    await websocket.send_json(created_envelope.model_dump(mode="json"))

    try:
        while True:
            try:
                raw_text = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {current_session_id}")
                break

            # 1. Safe JSON deserialization
            try:
                data = json.loads(raw_text)
                if not isinstance(data, dict):
                    raise ValueError("Root JSON value must be an object")
            except Exception as exc:
                error_frame = OutboundEnvelope(
                    type=OutboundMessageType.ERROR,
                    session_id=current_session_id,
                    payload=ErrorPayload(
                        code="INVALID_PAYLOAD",
                        message=f"Malformed JSON envelope: {exc}",
                        recoverable=True,
                    ).model_dump(mode="json"),
                )
                await websocket.send_json(error_frame.model_dump(mode="json"))
                continue

            # 2. Pydantic schema validation
            try:
                inbound = InboundEnvelope.model_validate(data)
            except ValidationError as exc:
                error_frame = OutboundEnvelope(
                    type=OutboundMessageType.ERROR,
                    session_id=current_session_id,
                    payload=ErrorPayload(
                        code="INVALID_PAYLOAD",
                        message=f"Envelope validation error: {exc}",
                        recoverable=True,
                    ).model_dump(mode="json"),
                )
                await websocket.send_json(error_frame.model_dump(mode="json"))
                continue

            # Check if inbound envelope explicitly targets or switches session_id
            if inbound.session_id and inbound.session_id.strip():
                current_session_id = inbound.session_id.strip()
                session = conversation_manager.get_or_create_session(current_session_id)

            # 3. Protocol routing
            msg_type = (
                inbound.type.value
                if isinstance(inbound.type, InboundMessageType)
                else str(inbound.type)
            )

            if msg_type == InboundMessageType.PING.value:
                pong_frame = OutboundEnvelope(
                    type=OutboundMessageType.PONG,
                    session_id=current_session_id,
                    payload={"timestamp": time.time()},
                )
                await websocket.send_json(pong_frame.model_dump(mode="json"))
                continue

            elif msg_type == InboundMessageType.RESET_SESSION.value:
                conversation_manager.reset_session(current_session_id)
                reset_frame = OutboundEnvelope(
                    type=OutboundMessageType.SESSION_RESET,
                    session_id=current_session_id,
                    payload={"session_id": current_session_id, "status": "reset"},
                )
                await websocket.send_json(reset_frame.model_dump(mode="json"))
                continue

            elif msg_type == InboundMessageType.USER_MESSAGE.value:
                payload: Dict[str, Any] = inbound.payload or {}
                raw_user_text = payload.get("text")

                if (
                    raw_user_text is None
                    or not isinstance(raw_user_text, str)
                    or not raw_user_text.strip()
                ):
                    error_frame = OutboundEnvelope(
                        type=OutboundMessageType.ERROR,
                        session_id=current_session_id,
                        payload=ErrorPayload(
                            code="EMPTY_MESSAGE",
                            message="Message text cannot be empty",
                            recoverable=True,
                        ).model_dump(mode="json"),
                    )
                    await websocket.send_json(error_frame.model_dump(mode="json"))
                    continue

                user_text = raw_user_text.strip()
                conversation_manager.add_user_message(current_session_id, user_text)
                messages = conversation_manager.build_chat_payload(current_session_id)
                turn_id = f"turn_{uuid.uuid4().hex[:8]}"

                # Emit stream_start frame
                start_frame = OutboundEnvelope(
                    type=OutboundMessageType.STREAM_START,
                    session_id=current_session_id,
                    payload={"turn_id": turn_id},
                )
                await websocket.send_json(start_frame.model_dump(mode="json"))

                # Stream LLM tokens
                full_response: List[str] = []
                try:
                    async for token, end_payload in llm_engine.generate_stream(
                        messages=messages,
                        turn_id=turn_id,
                    ):
                        if token:
                            full_response.append(token)
                            token_frame = OutboundEnvelope(
                                type=OutboundMessageType.TOKEN,
                                session_id=current_session_id,
                                payload={"token": token, "turn_id": turn_id},
                            )
                            await websocket.send_json(token_frame.model_dump(mode="json"))

                        if end_payload is not None:
                            conversation_manager.add_assistant_message(
                                current_session_id, "".join(full_response)
                            )
                            end_frame = OutboundEnvelope(
                                type=OutboundMessageType.STREAM_END,
                                session_id=current_session_id,
                                payload=end_payload.model_dump(mode="json"),
                            )
                            await websocket.send_json(end_frame.model_dump(mode="json"))

                except LLMEngineError as exc:
                    logger.error(f"LLM engine error during streaming: {exc}")
                    error_frame = OutboundEnvelope(
                        type=OutboundMessageType.ERROR,
                        session_id=current_session_id,
                        payload=exc.to_error_payload().model_dump(mode="json"),
                    )
                    await websocket.send_json(error_frame.model_dump(mode="json"))
                except WebSocketDisconnect:
                    logger.info(
                        f"Client disconnected during streaming: {current_session_id}"
                    )
                    break
                except Exception as exc:
                    logger.error(f"Unexpected streaming exception: {exc}", exc_info=True)
                    error_frame = OutboundEnvelope(
                        type=OutboundMessageType.ERROR,
                        session_id=current_session_id,
                        payload=ErrorPayload(
                            code="INFERENCE_FAILED",
                            message=f"Inference stream failed: {exc}",
                            recoverable=True,
                        ).model_dump(mode="json"),
                    )
                    await websocket.send_json(error_frame.model_dump(mode="json"))

            else:
                error_frame = OutboundEnvelope(
                    type=OutboundMessageType.ERROR,
                    session_id=current_session_id,
                    payload=ErrorPayload(
                        code="INVALID_PAYLOAD",
                        message=f"Unsupported message type: '{msg_type}'",
                        recoverable=True,
                    ).model_dump(mode="json"),
                )
                await websocket.send_json(error_frame.model_dump(mode="json"))
                continue

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {current_session_id}")
    except Exception as exc:
        logger.error(f"Unhandled WebSocket error: {exc}", exc_info=True)
