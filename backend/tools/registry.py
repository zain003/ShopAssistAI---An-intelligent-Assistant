"""Tool registry for ShopAssist AI."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from backend.tools.base import Tool
from backend.tools.calculate import CalculateTool
from backend.tools.crm import CRMMemoryTool
from backend.tools.lookup_order import LookupOrderTool
from backend.tools.search_catalog import SearchCatalogTool


class ToolRegistry:
    """Named collection of callable tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def schemas(self) -> List[Dict]:
        return [tool.schema() for tool in self._tools.values()]

    def schemas_xml(self) -> str:
        """Render tool schemas as XML for the system prompt."""
        lines = ["<available_tools>"]
        for tool in self._tools.values():
            schema_json = json.dumps(tool.parameters_schema, ensure_ascii=False)
            lines.append(
                f'  <tool name="{tool.name}">\n'
                f"    <description>{tool.description}</description>\n"
                f"    <parameters_schema>{schema_json}</parameters_schema>\n"
                f"  </tool>"
            )
        lines.append("</available_tools>")
        return "\n".join(lines)


def build_default_registry(crm_store_path: Optional[str] = None) -> ToolRegistry:
    """Build the Assignment 3 default tool set (3 core + CRM bonus)."""
    registry = ToolRegistry()
    registry.register(LookupOrderTool())
    registry.register(SearchCatalogTool())
    registry.register(CalculateTool())
    registry.register(CRMMemoryTool(store_path=crm_store_path))
    return registry
