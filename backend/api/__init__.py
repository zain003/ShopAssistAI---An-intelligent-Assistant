"""FastAPI backend API package for ShopAssist AI.

Exposes application instance and factory per FEAT-003-BE.
"""

from backend.api.main import app, create_app

__all__ = ["app", "create_app"]
