"""FastAPI application entrypoint and lifecycle coordinator for ShopAssist AI.

Configures CORS middleware, registers routers, and manages engine lifespan per FEAT-003-BE.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.api.websocket import router as ws_router
from backend.conversation.manager import ConversationManager
from backend.core.llm import LLMEngine

logger = logging.getLogger("backend.api")


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

    return app


app = create_app()
