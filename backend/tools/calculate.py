"""Safe mathematical expression evaluator for store totals / refunds."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any, Dict, Union

from backend.tools.base import Tool

Number = Union[int, float]

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_ALLOWED_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
}


class CalculateTool(Tool):
    """Evaluate a safe arithmetic expression (order totals, tax, shipping)."""

    name = "calculate"
    description = (
        "Evaluate a mathematical expression for order totals, refunds, discounts, "
        "or shipping fees. Supports +, -, *, /, //, %, **, parentheses, and "
        "abs/round/min/max/sqrt. Example: '(129.99 + 5.99) * 1.08'."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Arithmetic expression to evaluate.",
            }
        },
        "required": ["expression"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        expression = str(kwargs.get("expression", "")).strip()
        if not expression:
            return {"ok": False, "error": "expression is required"}
        if len(expression) > 200:
            return {"ok": False, "error": "expression is too long"}

        try:
            result = _safe_eval(expression)
            if isinstance(result, float):
                result = round(result, 4)
            return {"ok": True, "expression": expression, "result": result}
        except Exception as exc:
            return {"ok": False, "error": f"Could not evaluate expression: {exc}"}


def _safe_eval(expression: str) -> Number:
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("Only numeric literals are allowed")

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and (abs(left) > 1e6 or abs(right) > 10):
            raise ValueError("exponentiation out of safe range")
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise ZeroDivisionError("division by zero")
        return _BINARY_OPS[type(node.op)](left, right)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
            raise ValueError("function not allowed")
        args = [_eval_node(a) for a in node.args]
        if node.keywords:
            raise ValueError("keyword arguments not allowed")
        return _ALLOWED_FUNCS[node.func.id](*args)

    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    raise ValueError(f"unsupported expression node: {type(node).__name__}")
