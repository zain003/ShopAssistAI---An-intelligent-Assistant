"""Structured XML system prompt orchestrator for ShopAssist AI.

Assembles system prompts embedding domain persona, catalog products, customer orders,
store return/shipping policies, and deflection guardrails without external tools or RAG.
"""

from typing import Optional

from backend.conversation.data import (
    CATALOG_PRODUCTS,
    DEFLECTION_DIRECTIVE,
    MOCK_ORDERS,
    MOCK_ORDERS_BY_ID,
    STORE_PERSONA,
    STORE_POLICIES,
)


def _format_catalog_xml() -> str:
    """Formats catalog products into structured XML.

    Returns:
        XML string containing all catalog products with specs and availability.
    """
    lines = ["<catalog_products>"]
    for product in CATALOG_PRODUCTS:
        stock_status = f"In Stock ({product.stock_count} units)" if product.in_stock else "Out of Stock"
        features_str = "; ".join(product.features)
        lines.append(
            f'  <product sku="{product.sku}" name="{product.name}" category="{product.category}" '
            f'price="${product.price:.2f}" stock_status="{stock_status}" '
            f'warranty="{product.warranty_months} months" returnable="{product.returnable}">'
        )
        lines.append(f"    <features>{features_str}</features>")
        lines.append("  </product>")
    lines.append("</catalog_products>")
    return "\n".join(lines)


def _format_orders_xml() -> str:
    """Formats mock orders into structured XML.

    Returns:
        XML string containing mock orders with shipment and line item details.
    """
    lines = ["<mock_orders>"]
    for order in MOCK_ORDERS:
        items_summary = ", ".join(
            f"{item.quantity}x {item.name} (${item.unit_price:.2f})"
            for item in order.items
        )
        carrier_str = order.carrier or "Pending Carrier Assignment"
        tracking_str = order.tracking_number or "Pending Tracking"
        est_deliv = order.estimated_delivery or "Pending Schedule"
        return_str = order.return_eligible_until or "Ineligible / Pending Delivery"

        lines.append(
            f'  <order id="{order.order_id}" customer="{order.customer_name}" email="{order.customer_email}" '
            f'status="{order.status.value}" order_date="{order.order_date}" '
            f'carrier="{carrier_str}" tracking="{tracking_str}" '
            f'estimated_delivery="{est_deliv}" total="${order.total_amount:.2f}">'
        )
        lines.append(f"    <items>{items_summary}</items>")
        lines.append(f"    <shipping_address>{order.shipping_address}</shipping_address>")
        lines.append(f"    <return_eligible_until>{return_str}</return_eligible_until>")
        lines.append("  </order>")
    lines.append("</mock_orders>")
    return "\n".join(lines)


def render_system_prompt(active_order_id: Optional[str] = None) -> str:
    """Renders the complete structured XML system prompt for LLM inference.

    Constructs a comprehensive domain prompt embedding persona, product catalog,
    mock order records, store policies, active session focus, and explicit
    out-of-domain deflection rules per FEAT-002-BE.

    Args:
        active_order_id: Optional order ID currently referenced in the session
            (e.g., 'ORD-1085') to provide immediate contextual focus.

    Returns:
        str: Fully rendered XML prompt ready for injection at index 0 of chat payload.
    """
    catalog_xml = _format_catalog_xml()
    orders_xml = _format_orders_xml()

    active_order_section = ""
    if active_order_id:
        normalized_id = active_order_id.strip().upper()
        if not normalized_id.startswith("ORD-") and normalized_id.isdigit():
            normalized_id = f"ORD-{normalized_id}"

        order_record = MOCK_ORDERS_BY_ID.get(normalized_id)
        if order_record:
            items_str = ", ".join(f"{it.quantity}x {it.name}" for it in order_record.items)
            active_order_section = (
                f'\n<active_session_order id="{order_record.order_id}">\n'
                f"  <customer>{order_record.customer_name} ({order_record.customer_email})</customer>\n"
                f"  <status>{order_record.status.value}</status>\n"
                f"  <carrier>{order_record.carrier or 'N/A'}</carrier>\n"
                f"  <tracking>{order_record.tracking_number or 'N/A'}</tracking>\n"
                f"  <delivery_estimate>{order_record.estimated_delivery or 'N/A'}</delivery_estimate>\n"
                f"  <items>{items_str}</items>\n"
                "</active_session_order>\n"
            )

    prompt = f"""
<store_persona>
{STORE_PERSONA}
</store_persona>

{catalog_xml}

{orders_xml}
{active_order_section}
{STORE_POLICIES}

<deflection_rules>
{DEFLECTION_DIRECTIVE}
</deflection_rules>

<conversation_instructions>
1. Always address customers with courtesy and warmth.
2. When answering order status inquiries, clearly list Status, Carrier, Tracking Number, and Estimated Delivery.
3. When recommending products, highlight price, key features, and in-stock status.
4. When answering return or refund questions, explain the 30-day window and item condition requirements.
5. If the customer asks about anything outside of this store's products, orders, returns, or shipping, politely refuse and redirect to store support:
   "I can only assist with questions regarding our store's products, orders, returns, and shipping policies."
</conversation_instructions>
""".strip()

    return prompt
