"""Order lookup tool backed by mock order records."""

from __future__ import annotations

from typing import Any, Dict

from backend.conversation.data import MOCK_ORDERS_BY_ID
from backend.tools.base import Tool


class LookupOrderTool(Tool):
    """Fetch live-style order status by ORD-XXXX id."""

    name = "lookup_order"
    description = (
        "Look up a customer order by order ID (e.g. ORD-1085). "
        "Returns status, carrier, tracking number, items, totals, and delivery estimate."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Order ID in ORD-XXXX format (digits alone also accepted).",
            }
        },
        "required": ["order_id"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        raw = str(kwargs.get("order_id", "")).strip().upper()
        if not raw:
            return {"ok": False, "error": "order_id is required"}

        if not raw.startswith("ORD-"):
            digits = "".join(c for c in raw if c.isdigit())
            if len(digits) >= 4:
                raw = f"ORD-{digits[-4:]}"
            elif digits:
                raw = f"ORD-{digits.zfill(4)}"

        order = MOCK_ORDERS_BY_ID.get(raw)
        if order is None:
            return {
                "ok": False,
                "error": f"Order {raw} was not found. Valid examples: ORD-1001 … ORD-1085.",
            }

        return {
            "ok": True,
            "order_id": order.order_id,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "status": order.status.value,
            "carrier": order.carrier,
            "tracking_number": order.tracking_number,
            "order_date": order.order_date,
            "estimated_delivery": order.estimated_delivery,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "return_eligible_until": order.return_eligible_until,
            "items": [
                {
                    "sku": item.sku,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in order.items
            ],
        }
