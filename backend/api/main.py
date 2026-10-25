"""FastAPI application entrypoint and lifecycle coordinator for ShopAssist AI.

Configures CORS middleware, registers routers, and manages engine lifespan per FEAT-003-BE.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router as api_router
from backend.api.websocket import router as ws_router
from backend.conversation.manager import ConversationManager, RAGConversationManager
from backend.core.llm import LLMEngine
from backend.tools.orchestrator import ToolOrchestrator
from backend.tools.registry import build_default_registry
from backend.voice.pipeline import VoicePipeline

logger = logging.getLogger("backend.api")

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_DEFAULT_VECTOR_STORE_DIR = os.path.join(_PROJECT_ROOT, "data", "vector_store")


def _init_rag_manager(
    conversation_manager: ConversationManager,
    store_dir: Optional[str] = None,
) -> Optional[RAGConversationManager]:
    """Load the CPU vector store and wire RAGConversationManager, or return None on failure."""
    try:
        from backend.rag.retriever import VectorRetriever
        from backend.rag.vector_store import CPUVectorStore

        path = store_dir or _DEFAULT_VECTOR_STORE_DIR
        store = CPUVectorStore(embedding_dim=384)
        store.load(path)
        retriever = VectorRetriever(vector_store=store)
        retriever.warmup()
        logger.info("RAG ready: loaded %d chunks from %s", store.size(), path)
        return RAGConversationManager(
            base_manager=conversation_manager, retriever=retriever
        )
    except Exception as exc:
        logger.warning(
            "RAG initialization skipped; chat will run without retrieval: %s", exc
        )
        return None


def create_app(
    llm_engine: Optional[LLMEngine] = None,
    conversation_manager: Optional[ConversationManager] = None,
) -> FastAPI:
    """Application factory for ShopAssist AI FastAPI backend.

    Args:
        llm_engine: Optional LLMEngine instance for dependency injection.
        conversation_manager: Optional ConversationManager instance.

    Returns:
        FastAPI application configured with CORS, routes, and lifespan.
    """
    engine = llm_engine or LLMEngine()
    manager = conversation_manager or ConversationManager()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """FastAPI lifespan managing engine warmup and resource cleanup."""
        logger.info("Initializing ShopAssist AI application lifespan...")
        app.state.llm_engine = engine
        app.state.conversation_manager = manager

        # Load offline vector index and attach RAG manager (falls back gracefully)
        if getattr(app.state, "rag_manager", None) is None:
            app.state.rag_manager = _init_rag_manager(manager)

        # Assignment 3 — tools + local voice pipeline
        if getattr(app.state, "tool_orchestrator", None) is None:
            registry = build_default_registry()
            app.state.tool_orchestrator = ToolOrchestrator(registry, timeout_seconds=2.0)
            logger.info(
                "Tool orchestrator ready: %s",
                ", ".join(t.name for t in registry.list_tools()),
            )

        if getattr(app.state, "voice_pipeline", None) is None:
            app.state.voice_pipeline = VoicePipeline()
            # Optional eager load (can download models). Default: lazy on first use.
            if os.getenv("VOICE_WARMUP", "0").strip() in ("1", "true", "yes"):
                try:
                    await app.state.voice_pipeline.warmup()
                    logger.info("Voice pipeline warmup completed.")
                except Exception as exc:
                    logger.warning("Voice pipeline warmup skipped or failed: %s", exc)
            else:
                logger.info("Voice pipeline ready (lazy ASR/TTS load on first use).")

        # Perform fast startup warmup if Ollama service and model are ready
        try:
            is_ready = await engine.is_ready()
            if is_ready:
                logger.info(f"Ollama is ready. Pre-warming model '{engine.model}'...")
                await engine.warmup()
                logger.info("Model warmup completed successfully.")
            else:
                logger.warning(
                    f"Ollama model '{engine.model}' is not ready at startup. Warmup skipped."
                )
        except Exception as exc:
            logger.warning(f"Engine startup warmup skipped or failed: {exc}")

        yield

        logger.info("Shutting down ShopAssist AI application...")
        try:
            await engine.aclose()
        except Exception as exc:
            logger.warning(f"Error during LLMEngine shutdown: {exc}")

    app = FastAPI(
        title="ShopAssist AI API",
        description="FastAPI WebSocket & REST Streaming API for ShopAssist AI",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Attach to state immediately so non-lifespan test executions have references
    app.state.llm_engine = engine
    app.state.conversation_manager = manager
    app.state.rag_manager = None
    app.state.tool_orchestrator = ToolOrchestrator(
        build_default_registry(), timeout_seconds=2.0
    )
    app.state.voice_pipeline = VoicePipeline()

    # Configure CORS for local web interface development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routes
    app.include_router(api_router)
    app.include_router(ws_router)

    # Mount static files for web chat interface if frontend directory exists
    frontend_dir = os.path.join(_PROJECT_ROOT, "frontend")
    if os.path.isdir(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()
