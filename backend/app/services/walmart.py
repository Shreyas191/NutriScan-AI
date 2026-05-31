"""
Walmart Integration — builds shopping search URLs for recommendations.

Falls back gracefully: uses search URLs since Walmart has no public
shopping-list API equivalent to a dedicated developer platform.
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus
from typing import Any

from app.models.biomarker import FoodRecommendation

logger = logging.getLogger(__name__)

WALMART_SEARCH_BASE = "https://www.walmart.com/search?q="


def build_item_url(item_name: str) -> str:
    """Build a Walmart search URL for a single item."""
    return f"{WALMART_SEARCH_BASE}{quote_plus(item_name)}"


def build_cart_urls(recommendations: list[FoodRecommendation]) -> list[dict]:
    """Build Walmart search URLs for each recommendation."""
    return [
        {
            "name": rec.name,
            "emoji": rec.emoji,
            "nutrient": rec.nutrient,
            "amount": rec.amount,
            "category": rec.category,
            "walmart_url": build_item_url(rec.name),
        }
        for rec in recommendations
    ]


def build_shop_all_url(recommendations: list[FoodRecommendation]) -> str:
    """Build a combined Walmart search URL for all food items."""
    food_items = [r for r in recommendations if r.category == "food"]
    query = " ".join(r.name for r in food_items[:10])
    return f"{WALMART_SEARCH_BASE}{quote_plus(query)}"


async def create_shopping_list(
    recommendations: list[FoodRecommendation],
    title: str = "NutriScan AI — Your Personalized Grocery List",
) -> dict[str, Any]:
    """
    Build a Walmart shopping list from food recommendations.
    Returns cart_items with per-item search URLs and a shop_all_url.
    """
    cart_items = build_cart_urls(recommendations)
    shop_all_url = build_shop_all_url(recommendations)
    return {
        "cart_items": cart_items,
        "shop_all_url": shop_all_url,
        "api_used": False,
    }
