"""Prompt-based tool orchestrator with timeouts and graceful failures."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.tools.registry import ToolRegistry

logger = logging.getLogger("backend.tools.orchestrator")

_TOOL_CALL_PATTERN = re.compile(
    r"\{[^{}]*\"tool\"\s*:\s*\"([a-zA-Z0-9_]+)\"[^{}]*\}",
    re.DOTALL,
)

TOOL_CALL_INSTRUCTIONS = """
<tool_calling_rules>
You have access to tools listed in <available_tools>. When a tool is needed to answer
accurately (order lookup, catalog search, math, or CRM memory), reply with ONLY a JSON
object on a single line in this exact shape (no markdown, no explanation):
{"tool": "<tool_name>", "args": { ... }}

Rules:
- Use lookup_order when the customer asks about a specific order status/tracking.
- Use search_catalog when looking up products by name, SKU, or category.
- Use calculate for arithmetic on prices, totals, tax, refunds, or shipping fees.
- Use crm_memory with action=get when greeting a returning customer; action=update when
  they share name, email, phone, preferences, or a new request summary. Pass session_id
  from the conversation when available.
- If no tool is needed, answer the customer normally in plain prose (do NOT emit tool JSON).
- Never invent tool results; wait for <tool_result> if you requested a tool.
</tool_calling_rules>
""".strip()


class ToolOrchestrator:
    """Detect tool calls, execute with timeout, return results to the LLM."""

    def __init__(
        self,
        registry: ToolRegistry,
        timeout_seconds: float = 2.0,
        max_rounds: int = 2,
    ) -> None:
        self.registry = registry
        self.timeout_seconds = timeout_seconds
        self.max_rounds = max_rounds

    def format_tools_for_prompt(self) -> str:
        return f"{self.registry.schemas_xml()}\n\n{TOOL_CALL_INSTRUCTIONS}"

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a tool call JSON object from model output, if present."""
        raw = (text or "").strip()
        if not raw:
            return None

        # Strip markdown fences if the model wraps JSON
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if fence:
            raw = fence.group(1).strip()

        # Prefer first JSON object containing "tool"
        candidates: List[str] = []
        if raw.startswith("{") and raw.endswith("}"):
            candidates.append(raw)
        for match in re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw, re.DOTALL):
            candidates.append(match.group(0))

        for candidate in candidates:
            try:
                obj = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "tool" in obj:
                tool_name = str(obj.get("tool", "")).strip()
                args = obj.get("args") or obj.get("arguments") or {}
                if not isinstance(args, dict):
                    args = {}
                if tool_name:
                    return {"tool": tool_name, "args": args}
        return None

    async def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], float]:
        """Execute a named tool with timeout. Returns (result, elapsed_ms)."""
        started = time.perf_counter()
        tool = self.registry.get(tool_name)
        if tool is None:
            result = {
                "ok": False,
                "error": f"Unknown tool '{tool_name}'. Available: "
                f"{', '.join(t.name for t in self.registry.list_tools())}",
            }
            return result, (time.perf_counter() - started) * 1000.0

        try:
            result = await asyncio.wait_for(
                tool.execute(**args),
                timeout=self.timeout_seconds,
            )
            if not isinstance(result, dict):
                result = {"ok": True, "result": result}
        except asyncio.TimeoutError:
            logger.warning("Tool %s timed out after %.1fs", tool_name, self.timeout_seconds)
            result = {
                "ok": False,
                "error": (
                    f"Tool '{tool_name}' timed out after {self.timeout_seconds:.0f}s. "
                    "Please try again or answer without that tool."
                ),
            }
        except Exception as exc:
            logger.exception("Tool %s failed: %s", tool_name, exc)
            result = {
                "ok": False,
                "error": f"Tool '{tool_name}' failed: {exc}",
            }

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return result, elapsed_ms

    def format_tool_result_message(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Dict[str, Any],
    ) -> str:
        payload = json.dumps(result, ensure_ascii=False, default=str)
        args_json = json.dumps(args, ensure_ascii=False, default=str)
        return (
            f'<tool_result name="{tool_name}" args=\'{args_json}\'>\n'
            f"{payload}\n"
            f"</tool_result>\n"
            "Using the tool result above, answer the customer in clear natural language. "
            "Do not emit another tool JSON unless a different tool is truly required."
        )

    async def run_tool_round(
        self,
        model_text: str,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Parse and execute one tool call from model text.

        Returns dict with keys: tool, args, result, elapsed_ms — or None if no call.
        """
        parsed = self.parse_tool_call(model_text)
        if not parsed:
            return None

        args = dict(parsed["args"])
        if extra_args:
            # Inject session context for CRM without requiring the model to invent it
            for key, value in extra_args.items():
                args.setdefault(key, value)

        result, elapsed_ms = await self.execute_tool(parsed["tool"], args)
        return {
            "tool": parsed["tool"],
            "args": args,
            "result": result,
            "elapsed_ms": round(elapsed_ms, 2),
        }
