"""Configuration settings for LLM engine and backend services."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """System settings with environment variable fallbacks."""

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    MODEL_NAME: str = os.getenv("MODEL_NAME", os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"))
    DEFAULT_TIMEOUT: float = float(os.getenv("DEFAULT_TIMEOUT", "60.0"))
    READY_TIMEOUT: float = float(os.getenv("READY_TIMEOUT", "2.0"))


settings = Settings()

# Exposed constants
OLLAMA_BASE_URL: str = settings.OLLAMA_BASE_URL
OLLAMA_MODEL: str = settings.OLLAMA_MODEL
MODEL_NAME: str = settings.MODEL_NAME
DEFAULT_TIMEOUT: float = settings.DEFAULT_TIMEOUT
READY_TIMEOUT: float = settings.READY_TIMEOUT
