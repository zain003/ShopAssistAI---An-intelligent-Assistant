"""FastAPI WebSocket chat streaming endpoint for ShopAssist AI.

Implements bidirectional JSON envelope protocol, token-by-token streaming,
session state coordination, tool orchestration, and local voice (ASR/TTS)
per FEAT-003-BE and Assignment 3. Existing text contract is preserved; audio
events are additive.
"""

from __future__ import annotations

import base64
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
from backend.conversation.deflection import (
    STORE_REFUSAL_MESSAGE,
    response_has_off_topic_leakage,
    should_hard_deflect,
)
from backend.conversation.manager import ConversationManager
from backend.core.llm import LLMEngine, LLMEngineError
from backend.tools.orchestrator import ToolOrchestrator
from backend.voice.pipeline import VoicePipeline, VoiceSessionBuffer
from backend.voice.sentences import SentenceBuffer

logger = logging.getLogger("backend.api.websocket")

router = APIRouter(tags=["WebSocket"])


async def _send(
    websocket: WebSocket,
    msg_type: OutboundMessageType,
    session_id: str,
    payload: Dict[str, Any],
) -> None:
    envelope = OutboundEnvelope(
        type=msg_type,
        session_id=session_id,
        payload=payload,
    )
    await websocket.send_json(envelope.model_dump(mode="json"))


async def _send_error(
    websocket: WebSocket,
    session_id: str,
    code: str,
    message: str,
    recoverable: bool = True,
) -> None:
    await _send(
        websocket,
        OutboundMessageType.ERROR,
        session_id,
        ErrorPayload(code=code, message=message, recoverable=recoverable).model_dump(
            mode="json"
        ),
    )


async def _maybe_speak_sentences(
    websocket: WebSocket,
    session_id: str,
    turn_id: str,
    voice: Optional[VoicePipeline],
    enable_tts: bool,
    sentence_buf: SentenceBuffer,
    token_text: str,
    *,
    flush: bool = False,
    speech_end_t: Optional[float] = None,
    first_audio_ms_holder: Optional[Dict[str, float]] = None,
) -> None:
    if not enable_tts or voice is None:
        return
    sentences = sentence_buf.flush() if flush else sentence_buf.push(token_text)
    for sentence in sentences:
        try:
            wav, sample_rate, _synth_ms, backend = await voice.tts.synthesize(sentence)
        except Exception as exc:
            logger.warning("TTS failed for sentence: %s", exc)
            continue
        if not wav:
            continue
        if first_audio_ms_holder is not None and "tts_first_audio_ms" not in first_audio_ms_holder:
            # Relative to stream start is filled by caller; mark absolute now
            first_audio_ms_holder["tts_first_audio_at"] = time.perf_counter()
            if speech_end_t is not None:
                first_audio_ms_holder["end_of_speech_to_first_audio_ms"] = (
                    time.perf_counter() - speech_end_t
                ) * 1000.0
        await _send(
            websocket,
            OutboundMessageType.TTS_AUDIO_CHUNK,
            session_id,
            {
                "turn_id": turn_id,
                "audio_b64": base64.b64encode(wav).decode("ascii"),
                "format": "wav",
                "sample_rate": sample_rate,
                "text": sentence,
                "backend": backend,
            },
        )


async def handle_user_turn(
    websocket: WebSocket,
    *,
    conversation_manager: ConversationManager,
    llm_engine: LLMEngine,
    session_id: str,
    user_text: str,
    tool_orchestrator: Optional[ToolOrchestrator] = None,
    voice: Optional[VoicePipeline] = None,
    enable_tts: bool = False,
    asr_ms: Optional[float] = None,
    speech_end_t: Optional[float] = None,
) -> None:
    """Shared path for typed and spoken turns (RAG + tools + stream + optional TTS)."""
    conversation_manager.add_user_message(session_id, user_text)

    rag_manager = getattr(websocket.app.state, "rag_manager", None)
    retrieval_ms: Optional[float] = None
    citations_list: List[Dict[str, Any]] = []
    is_fallback: Optional[bool] = None
    tools_xml = (
        tool_orchestrator.format_tools_for_prompt() if tool_orchestrator else None
    )

    if rag_manager is not None:
        messages, retrieval_res = await rag_manager.build_rag_chat_payload(
            session_id, user_text, tools_xml=tools_xml
        )
        retrieval_ms = retrieval_res.retrieval_ms
        citations_list = [c.model_dump(mode="json") for c in retrieval_res.citations]
        is_fallback = retrieval_res.is_fallback
    else:
        messages = conversation_manager.build_chat_payload(
            session_id, tools_xml=tools_xml
        )

    turn_id = f"turn_{uuid.uuid4().hex[:8]}"
    await _send(
        websocket,
        OutboundMessageType.STREAM_START,
        session_id,
        {"turn_id": turn_id},
    )

    if should_hard_deflect(user_text, is_fallback):
        conversation_manager.add_assistant_message(session_id, STORE_REFUSAL_MESSAGE)
        await _send(
            websocket,
            OutboundMessageType.TOKEN,
            session_id,
            {"token": STORE_REFUSAL_MESSAGE, "turn_id": turn_id},
        )
        if enable_tts and voice is not None:
            try:
                wav, sample_rate, _, backend = await voice.tts.synthesize(
                    STORE_REFUSAL_MESSAGE
                )
                if wav:
                    await _send(
                        websocket,
                        OutboundMessageType.TTS_AUDIO_CHUNK,
                        session_id,
                        {
                            "turn_id": turn_id,
                            "audio_b64": base64.b64encode(wav).decode("ascii"),
                            "format": "wav",
                            "sample_rate": sample_rate,
                            "text": STORE_REFUSAL_MESSAGE,
                            "backend": backend,
                        },
                    )
                    await _send(
                        websocket,
                        OutboundMessageType.TTS_END,
                        session_id,
                        {"turn_id": turn_id},
                    )
            except Exception as exc:
                logger.warning("TTS on refusal failed: %s", exc)
        end_payload_dict: Dict[str, Any] = {
            "turn_id": turn_id,
            "total_tokens": len(STORE_REFUSAL_MESSAGE.split()),
            "ttft_ms": 0.0,
            "total_duration_ms": 0.0,
            "tokens_per_second": 0.0,
            "is_fallback": True,
            "citations": [],
        }
        if retrieval_ms is not None:
            end_payload_dict["retrieval_ms"] = retrieval_ms
        if asr_ms is not None:
            end_payload_dict["asr_ms"] = asr_ms
        await _send(
            websocket, OutboundMessageType.STREAM_END, session_id, end_payload_dict
        )
        return

    tool_ms_total = 0.0
    direct_answer: Optional[str] = None
    # Prompt-based tool loop (up to max_rounds)
    if tool_orchestrator is not None:
        session = conversation_manager.get_or_create_session(session_id)
        extra_args = {
            "session_id": session_id,
            "user_id": session.active_customer_email or session_id,
        }
        for _ in range(tool_orchestrator.max_rounds):
            try:
                probe = await llm_engine.generate_complete(
                    messages=messages, temperature=0.1, max_tokens=200
                )
            except (LLMEngineError, Exception) as exc:
                logger.warning("Tool probe failed: %s", exc)
                break

            call = await tool_orchestrator.run_tool_round(probe, extra_args=extra_args)
            if call is None:
                # No tool needed — reuse probe text (avoid a second LLM round)
                if probe and probe.strip() and not tool_orchestrator.parse_tool_call(probe):
                    direct_answer = probe.strip()
                break

            tool_ms_total += float(call["elapsed_ms"])
            await _send(
                websocket,
                OutboundMessageType.TOOL_CALL,
                session_id,
                {
                    "turn_id": turn_id,
                    "tool": call["tool"],
                    "args": call["args"],
                },
            )
            await _send(
                websocket,
                OutboundMessageType.TOOL_RESULT,
                session_id,
                {
                    "turn_id": turn_id,
                    "tool": call["tool"],
                    "result": call["result"],
                    "elapsed_ms": call["elapsed_ms"],
                },
            )
            result_msg = tool_orchestrator.format_tool_result_message(
                call["tool"], call["args"], call["result"]
            )
            messages.append({"role": "assistant", "content": probe.strip()})
            messages.append({"role": "user", "content": result_msg})

    buffer_fallback = bool(is_fallback)
    full_response: List[str] = []
    sentence_buf = SentenceBuffer()
    stream_t0 = time.perf_counter()
    first_audio_holder: Dict[str, float] = {}

    async def _finish_turn(assistant_text: str, end_payload_dict: Dict[str, Any]) -> None:
        if buffer_fallback and response_has_off_topic_leakage(assistant_text):
            assistant_text = STORE_REFUSAL_MESSAGE

        await _maybe_speak_sentences(
            websocket,
            session_id,
            turn_id,
            voice,
            enable_tts,
            sentence_buf,
            "",
            flush=True,
            speech_end_t=speech_end_t,
            first_audio_ms_holder=first_audio_holder,
        )
        if enable_tts and voice is not None:
            await _send(
                websocket,
                OutboundMessageType.TTS_END,
                session_id,
                {"turn_id": turn_id},
            )

        conversation_manager.add_assistant_message(session_id, assistant_text)
        if retrieval_ms is not None:
            end_payload_dict["retrieval_ms"] = retrieval_ms
        if citations_list:
            end_payload_dict["citations"] = citations_list
        if is_fallback is not None:
            end_payload_dict["is_fallback"] = is_fallback
        if asr_ms is not None:
            end_payload_dict["asr_ms"] = round(asr_ms, 2)
        if tool_ms_total > 0:
            end_payload_dict["tool_ms"] = round(tool_ms_total, 2)

        tts_at = first_audio_holder.get("tts_first_audio_at")
        if tts_at is not None:
            end_payload_dict["tts_first_audio_ms"] = round(
                (tts_at - stream_t0) * 1000.0, 2
            )
        if "end_of_speech_to_first_audio_ms" in first_audio_holder:
            end_payload_dict["end_of_speech_to_first_audio_ms"] = round(
                first_audio_holder["end_of_speech_to_first_audio_ms"], 2
            )

        await _send(
            websocket,
            OutboundMessageType.STREAM_END,
            session_id,
            end_payload_dict,
        )

    try:
        if direct_answer is not None:
            text = direct_answer
            if buffer_fallback and response_has_off_topic_leakage(text):
                text = STORE_REFUSAL_MESSAGE
            await _send(
                websocket,
                OutboundMessageType.TOKEN,
                session_id,
                {"token": text, "turn_id": turn_id},
            )
            await _maybe_speak_sentences(
                websocket,
                session_id,
                turn_id,
                voice,
                enable_tts,
                sentence_buf,
                text,
                speech_end_t=speech_end_t,
                first_audio_ms_holder=first_audio_holder,
            )
            await _finish_turn(
                text,
                {
                    "turn_id": turn_id,
                    "total_tokens": max(len(text.split()), 1),
                    "ttft_ms": round((time.perf_counter() - stream_t0) * 1000.0, 2),
                    "total_duration_ms": round(
                        (time.perf_counter() - stream_t0) * 1000.0, 2
                    ),
                    "tokens_per_second": 0.0,
                },
            )
            return

        async for token, end_payload in llm_engine.generate_stream(
            messages=messages,
            turn_id=turn_id,
        ):
            if token:
                full_response.append(token)
                if not buffer_fallback:
                    await _send(
                        websocket,
                        OutboundMessageType.TOKEN,
                        session_id,
                        {"token": token, "turn_id": turn_id},
                    )
                    await _maybe_speak_sentences(
                        websocket,
                        session_id,
                        turn_id,
                        voice,
                        enable_tts,
                        sentence_buf,
                        token,
                        speech_end_t=speech_end_t,
                        first_audio_ms_holder=first_audio_holder,
                    )

            if end_payload is not None:
                assistant_text = "".join(full_response).strip()
                if buffer_fallback:
                    if response_has_off_topic_leakage(assistant_text):
                        assistant_text = STORE_REFUSAL_MESSAGE
                    await _send(
                        websocket,
                        OutboundMessageType.TOKEN,
                        session_id,
                        {"token": assistant_text, "turn_id": turn_id},
                    )
                    await _maybe_speak_sentences(
                        websocket,
                        session_id,
                        turn_id,
                        voice,
                        enable_tts,
                        sentence_buf,
                        assistant_text,
                        speech_end_t=speech_end_t,
                        first_audio_ms_holder=first_audio_holder,
                    )

                end_payload_dict = end_payload.model_dump(mode="json")
                await _finish_turn(assistant_text, end_payload_dict)

    except LLMEngineError as exc:
        logger.error("LLM engine error during streaming: %s", exc)
        await _send(
            websocket,
            OutboundMessageType.ERROR,
            session_id,
            exc.to_error_payload().model_dump(mode="json"),
        )
    except WebSocketDisconnect:
        raise
    except Exception as exc:
        logger.error("Unexpected streaming exception: %s", exc, exc_info=True)
        await _send_error(
            websocket,
            session_id,
            "INFERENCE_FAILED",
            f"Inference stream failed: {exc}",
        )


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket) -> None:
    """Asynchronous WebSocket endpoint for real-time chat + voice streaming."""
    await websocket.accept()

    conversation_manager: ConversationManager = (
        getattr(websocket.app.state, "conversation_manager", None)
        or ConversationManager()
    )
    llm_engine: LLMEngine = (
        getattr(websocket.app.state, "llm_engine", None) or LLMEngine()
    )
    tool_orchestrator: Optional[ToolOrchestrator] = getattr(
        websocket.app.state, "tool_orchestrator", None
    )
    voice: Optional[VoicePipeline] = getattr(websocket.app.state, "voice_pipeline", None)

    query_session_id = websocket.query_params.get("session_id")
    initial_session_id = (
        query_session_id.strip()
        if (query_session_id and query_session_id.strip())
        else str(uuid.uuid4())
    )
    session = conversation_manager.get_or_create_session(initial_session_id)
    current_session_id = session.session_id

    audio_buffer = VoiceSessionBuffer()
    speech_end_t: Optional[float] = None

    await _send(
        websocket,
        OutboundMessageType.SESSION_CREATED,
        current_session_id,
        {"session_id": current_session_id},
    )

    try:
        while True:
            try:
                raw_text = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected: %s", current_session_id)
                break

            try:
                data = json.loads(raw_text)
                if not isinstance(data, dict):
                    raise ValueError("Root JSON value must be an object")
            except Exception as exc:
                await _send_error(
                    websocket,
                    current_session_id,
                    "INVALID_PAYLOAD",
                    f"Malformed JSON envelope: {exc}",
                )
                continue

            try:
                inbound = InboundEnvelope.model_validate(data)
            except ValidationError as exc:
                await _send_error(
                    websocket,
                    current_session_id,
                    "INVALID_PAYLOAD",
                    f"Envelope validation error: {exc}",
                )
                continue

            if inbound.session_id and inbound.session_id.strip():
                current_session_id = inbound.session_id.strip()
                session = conversation_manager.get_or_create_session(current_session_id)

            msg_type = (
                inbound.type.value
                if isinstance(inbound.type, InboundMessageType)
                else str(inbound.type)
            )

            if msg_type == InboundMessageType.PING.value:
                await _send(
                    websocket,
                    OutboundMessageType.PONG,
                    current_session_id,
                    {"timestamp": time.time()},
                )
                continue

            if msg_type == InboundMessageType.RESET_SESSION.value:
                conversation_manager.reset_session(current_session_id)
                audio_buffer.reset()
                speech_end_t = None
                await _send(
                    websocket,
                    OutboundMessageType.SESSION_RESET,
                    current_session_id,
                    {"session_id": current_session_id, "status": "reset"},
                )
                continue

            if msg_type == InboundMessageType.AUDIO_CHUNK.value:
                payload = inbound.payload or {}
                if voice is None:
                    await _send_error(
                        websocket,
                        current_session_id,
                        "ASR_UNAVAILABLE",
                        "Voice pipeline is not initialized on the server.",
                    )
                    continue
                pcm, sample_rate = VoicePipeline.decode_audio_payload(payload)
                ended = audio_buffer.add_chunk(pcm, sample_rate=sample_rate)
                # Optional interim transcript every N chunks is expensive; skip for latency
                if ended:
                    speech_end_t = time.perf_counter()
                    await _finalize_audio_turn(
                        websocket,
                        conversation_manager=conversation_manager,
                        llm_engine=llm_engine,
                        tool_orchestrator=tool_orchestrator,
                        voice=voice,
                        session_id=current_session_id,
                        audio_buffer=audio_buffer,
                        speech_end_t=speech_end_t,
                    )
                continue

            if msg_type == InboundMessageType.AUDIO_END.value:
                if voice is None:
                    await _send_error(
                        websocket,
                        current_session_id,
                        "ASR_UNAVAILABLE",
                        "Voice pipeline is not initialized on the server.",
                    )
                    continue
                speech_end_t = time.perf_counter()
                await _finalize_audio_turn(
                    websocket,
                    conversation_manager=conversation_manager,
                    llm_engine=llm_engine,
                    tool_orchestrator=tool_orchestrator,
                    voice=voice,
                    session_id=current_session_id,
                    audio_buffer=audio_buffer,
                    speech_end_t=speech_end_t,
                )
                continue

            if msg_type == InboundMessageType.USER_MESSAGE.value:
                payload = inbound.payload or {}
                raw_user_text = payload.get("text")
                if (
                    raw_user_text is None
                    or not isinstance(raw_user_text, str)
                    or not raw_user_text.strip()
                ):
                    await _send_error(
                        websocket,
                        current_session_id,
                        "EMPTY_MESSAGE",
                        "Message text cannot be empty",
                    )
                    continue

                enable_tts = bool(payload.get("enable_tts", False))
                try:
                    await handle_user_turn(
                        websocket,
                        conversation_manager=conversation_manager,
                        llm_engine=llm_engine,
                        session_id=current_session_id,
                        user_text=raw_user_text.strip(),
                        tool_orchestrator=tool_orchestrator,
                        voice=voice,
                        enable_tts=enable_tts,
                    )
                except WebSocketDisconnect:
                    logger.info(
                        "Client disconnected during streaming: %s", current_session_id
                    )
                    break
                continue

            await _send_error(
                websocket,
                current_session_id,
                "INVALID_PAYLOAD",
                f"Unsupported message type: '{msg_type}'",
            )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: %s", current_session_id)
    except Exception as exc:
        logger.error("Unhandled WebSocket error: %s", exc, exc_info=True)


async def _finalize_audio_turn(
    websocket: WebSocket,
    *,
    conversation_manager: ConversationManager,
    llm_engine: LLMEngine,
    tool_orchestrator: Optional[ToolOrchestrator],
    voice: VoicePipeline,
    session_id: str,
    audio_buffer: VoiceSessionBuffer,
    speech_end_t: float,
) -> None:
    """Run ASR on buffered audio and feed transcript into the shared turn handler."""
    pcm = audio_buffer.pcm()
    audio_buffer.reset()
    if not pcm:
        await _send_error(
            websocket,
            session_id,
            "EMPTY_AUDIO",
            "No audio received for this utterance.",
        )
        return

    try:
        transcript, asr_ms = await voice.transcribe_buffer(
            _buffer_from_pcm(pcm, 16000)
        )
    except Exception as exc:
        logger.exception("ASR failed: %s", exc)
        await _send_error(
            websocket,
            session_id,
            "ASR_FAILED",
            f"Speech recognition failed: {exc}",
        )
        return

    await _send(
        websocket,
        OutboundMessageType.ASR_FINAL,
        session_id,
        {"text": transcript, "asr_ms": round(asr_ms, 2)},
    )

    if not transcript.strip():
        await _send_error(
            websocket,
            session_id,
            "EMPTY_TRANSCRIPT",
            "Could not detect speech in the audio. Please try again.",
        )
        return

    await handle_user_turn(
        websocket,
        conversation_manager=conversation_manager,
        llm_engine=llm_engine,
        session_id=session_id,
        user_text=transcript.strip(),
        tool_orchestrator=tool_orchestrator,
        voice=voice,
        enable_tts=True,
        asr_ms=asr_ms,
        speech_end_t=speech_end_t,
    )


def _buffer_from_pcm(pcm: bytes, sample_rate: int) -> VoiceSessionBuffer:
    buf = VoiceSessionBuffer(sample_rate=sample_rate)
    buf.chunks = [pcm]
    return buf
