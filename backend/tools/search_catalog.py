"""Product catalog search tool."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.conversation.data import CATALOG_BY_SKU, CATALOG_PRODUCTS
from backend.tools.base import Tool


class SearchCatalogTool(Tool):
    """Search ApexStyle catalog by query, SKU, or category."""

    name = "search_catalog"
    description = (
        "Search the store product catalog by free-text query, SKU, or category. "
        "Returns matching products with price, stock, features, and warranty."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search text (product name, keyword, or SKU).",
            },
            "category": {
                "type": "string",
                "description": "Optional category filter (Audio, Wearables, Home & Office, Footwear).",
            },
            "limit": {
                "type": "integer",
                "description": "Max results to return (default 5).",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        query = str(kwargs.get("query", "")).strip()
        category = str(kwargs.get("category", "") or "").strip()
        try:
            limit = int(kwargs.get("limit", 5) or 5)
        except (TypeError, ValueError):
            limit = 5
        limit = max(1, min(limit, 10))

        if not query and not category:
            return {"ok": False, "error": "query or category is required"}

        # Exact SKU hit
        sku_key = query.upper()
        if sku_key in CATALOG_BY_SKU:
            product = CATALOG_BY_SKU[sku_key]
            return {"ok": True, "count": 1, "products": [_product_dict(product)]}

        q_lower = query.lower()
        cat_lower = category.lower()
        matches: List[Dict[str, Any]] = []

        for product in CATALOG_PRODUCTS:
            if cat_lower and cat_lower not in product.category.lower():
                continue
            haystack = " ".join(
                [
                    product.sku,
                    product.name,
                    product.category,
                    " ".join(product.features),
                ]
            ).lower()
            if q_lower and q_lower not in haystack:
                continue
            matches.append(_product_dict(product))
            if len(matches) >= limit:
                break

        if not matches and not q_lower and cat_lower:
            for product in CATALOG_PRODUCTS:
                if cat_lower in product.category.lower():
                    matches.append(_product_dict(product))
                    if len(matches) >= limit:
                        break

        return {
            "ok": True,
            "count": len(matches),
            "products": matches,
            "message": None if matches else "No catalog products matched that search.",
        }


def _product_dict(product: Any) -> Dict[str, Any]:
    return {
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "in_stock": product.in_stock,
        "stock_count": product.stock_count,
        "features": list(product.features),
        "warranty_months": product.warranty_months,
        "returnable": product.returnable,
    }
