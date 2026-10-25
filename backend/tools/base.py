"""Base tool protocol and shared result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Abstract tool the LLM can invoke via prompt-based function calling."""

    name: str
    description: str
    parameters_schema: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the tool and return a JSON-serializable result dict."""

    def schema(self) -> Dict[str, Any]:
        """Return OpenAI-style function schema for prompting."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema,
        }
