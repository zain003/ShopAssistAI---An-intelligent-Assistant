"""REST routes for ShopAssist AI backend.

Exposes health check and readiness probe per FEAT-003-BE.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Request

from backend.core.llm import LLMEngine

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """Health check and model readiness probe endpoint.

    Returns:
        Dict[str, Any]: Service health status, model identifier, and readiness flag.
    """
    engine: Optional[LLMEngine] = getattr(request.app.state, "llm_engine", None)
    if engine is not None:
        ready = await engine.is_ready()
        model = engine.model
    else:
        ready = False
        model = ""

    return {
        "status": "ok",
        "model": model,
        "ready": ready,
    }
