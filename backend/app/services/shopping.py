"""
Shopping Service — generates shopping links for multiple marketplaces.

Primary:  Instacart (Developer Platform API → shoppable list link, or search URLs)
Fallback: Amazon (search URLs)
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus
from typing import Any

from app.models.biomarker import FoodRecommendation
from app.services import instacart

logger = logging.getLogger(__name__)


async def create_shopping_links(
    recommendations: list[FoodRecommendation],
) -> dict[str, Any]:
    """
    Generate shopping links for all supported marketplaces.

    Returns a dict with:
      - cart_items: list of items with per-marketplace links
      - shopping_links: dict mapping marketplace_id -> shop_all_url
    """
    # 1. Instacart (primary) — real API list if key configured, else search URLs
    instacart_result = await instacart.create_shopping_list(recommendations)
    instacart_url = instacart_result["shop_all_url"]

    # 2. Amazon (fallback search URLs)
    amazon_url = _build_search_url("amazon", recommendations)

    # Consolidated cart items with links for each marketplace
    cart_items = []
    for rec in recommendations:
        cart_items.append({
            "name": rec.name,
            "emoji": rec.emoji,
            "nutrient": rec.nutrient,
            "amount": rec.amount,
            "category": rec.category,
            "links": {
                "instacart": instacart.build_item_url(rec.name),
                "amazon": _build_item_url("amazon", rec.name),
            },
        })

    return {
        "cart_items": cart_items,
        "shopping_links": {
            "instacart": instacart_url,
            "amazon": amazon_url,
        },
    }


def _build_search_url(marketplace: str, recommendations: list[FoodRecommendation]) -> str:
    food_items = [r for r in recommendations if r.category == "food"]
    query = quote_plus(" ".join(r.name for r in food_items[:10]))

    if marketplace == "amazon":
        return f"https://www.amazon.com/s?k={query}&i=grocery"

    return ""


def _build_item_url(marketplace: str, item_name: str) -> str:
    encoded = quote_plus(item_name)

    if marketplace == "amazon":
        return f"https://www.amazon.com/s?k={encoded}&i=grocery"

    return ""
