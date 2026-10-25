"""Unit tests for Assignment 3 tool registry and orchestrator."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile

import pytest

from backend.tools.calculate import CalculateTool
from backend.tools.crm import CRMMemoryTool
from backend.tools.lookup_order import LookupOrderTool
from backend.tools.orchestrator import ToolOrchestrator
from backend.tools.registry import build_default_registry
from backend.tools.search_catalog import SearchCatalogTool


@pytest.mark.asyncio
async def test_lookup_order_found():
    tool = LookupOrderTool()
    result = await tool.execute(order_id="ORD-1085")
    assert result["ok"] is True
    assert result["status"] == "In Transit"
    assert result["tracking_number"] == "FDX-992817264"


@pytest.mark.asyncio
async def test_lookup_order_digits_only():
    tool = LookupOrderTool()
    result = await tool.execute(order_id="1085")
    assert result["ok"] is True
    assert result["order_id"] == "ORD-1085"


@pytest.mark.asyncio
async def test_lookup_order_missing():
    tool = LookupOrderTool()
    result = await tool.execute(order_id="ORD-9999")
    assert result["ok"] is False
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_search_catalog_by_name():
    tool = SearchCatalogTool()
    result = await tool.execute(query="headphones")
    assert result["ok"] is True
    assert result["count"] >= 1
    assert any("SonicQuiet" in p["name"] for p in result["products"])


@pytest.mark.asyncio
async def test_search_catalog_by_sku():
    tool = SearchCatalogTool()
    result = await tool.execute(query="AUDIO-SQ-01")
    assert result["ok"] is True
    assert result["count"] == 1
    assert result["products"][0]["sku"] == "AUDIO-SQ-01"


@pytest.mark.asyncio
async def test_calculate_expression():
    tool = CalculateTool()
    result = await tool.execute(expression="(129.99 + 5.99) * 1.08")
    assert result["ok"] is True
    assert abs(result["result"] - 146.8584) < 0.01


@pytest.mark.asyncio
async def test_calculate_rejects_unsafe():
    tool = CalculateTool()
    result = await tool.execute(expression="__import__('os').system('echo hi')")
    assert result["ok"] is False


@pytest.mark.asyncio
async def test_crm_get_update_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "crm.json")
        tool = CRMMemoryTool(store_path=path)
        missing = await tool.execute(action="get", user_id="alice@example.com")
        assert missing["found"] is False

        updated = await tool.execute(
            action="update",
            user_id="alice@example.com",
            name="Alice",
            preferences="prefers express shipping",
            last_interaction="Asked about ORD-1085",
        )
        assert updated["ok"] is True
        assert updated["record"]["name"] == "Alice"

        got = await tool.execute(action="get", user_id="alice@example.com")
        assert got["found"] is True
        assert got["record"]["preferences"] == "prefers express shipping"


@pytest.mark.asyncio
async def test_orchestrator_parse_and_execute():
    registry = build_default_registry()
    orch = ToolOrchestrator(registry, timeout_seconds=2.0)
    parsed = orch.parse_tool_call(
        '{"tool": "lookup_order", "args": {"order_id": "ORD-1001"}}'
    )
    assert parsed is not None
    assert parsed["tool"] == "lookup_order"

    call = await orch.run_tool_round(
        '{"tool": "calculate", "args": {"expression": "10 + 5"}}'
    )
    assert call is not None
    assert call["result"]["ok"] is True
    assert call["result"]["result"] == 15
    assert call["elapsed_ms"] >= 0


@pytest.mark.asyncio
async def test_orchestrator_timeout():
    class SlowTool(LookupOrderTool):
        name = "slow_tool"
        description = "Slow test tool"
        parameters_schema = {"type": "object", "properties": {}, "required": []}

        async def execute(self, **kwargs):
            await asyncio.sleep(5)
            return {"ok": True}

    registry = build_default_registry()
    registry.register(SlowTool())
    orch = ToolOrchestrator(registry, timeout_seconds=0.2)
    result, elapsed = await orch.execute_tool("slow_tool", {})
    assert result["ok"] is False
    assert "timed out" in result["error"].lower()
    assert elapsed < 2000


def test_registry_schemas_xml():
    registry = build_default_registry()
    xml = registry.schemas_xml()
    assert "lookup_order" in xml
    assert "search_catalog" in xml
    assert "calculate" in xml
    assert "crm_memory" in xml
    schemas = registry.schemas()
    assert len(schemas) == 4
    for s in schemas:
        json.dumps(s)  # serializable
