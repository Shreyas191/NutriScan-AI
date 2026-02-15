"""
Instacart Integration — creates real shopping lists via Instacart Developer Platform API.

Uses POST /idp/v1/products/products_link to create a shoppable link.
Falls back to search URLs if API key is not configured or API call fails.
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus
from typing import Any

import httpx

from app.config import settings
from app.models.biomarker import FoodRecommendation

logger = logging.getLogger(__name__)

INSTACART_SEARCH_BASE = "https://www.instacart.com/store/search"


# ---------------------------------------------------------------------------
# Real API — Instacart Developer Platform
# ---------------------------------------------------------------------------

async def create_shopping_list(
    recommendations: list[FoodRecommendation],
    title: str = "NutriScan AI — Your Personalized Grocery List",
) -> dict[str, Any]:
    """
    Create a shopping list on Instacart via the Developer Platform API.

    Calls POST /idp/v1/products/products_link to generate a shareable link.
    Users who click the link can select a store, add products to cart, and checkout.

    Falls back to URL-based approach if API key is missing or API fails.

    Args:
        recommendations: List of food/supplement recommendations.
        title: Title for the shopping list page.

    Returns:
        Dict with cart_items list and shop_all_url.
    """
    # If no API key, fall back to URL-based approach
    if not settings.INSTACART_API_KEY:
        logger.info("No Instacart API key configured — using URL fallback")
        return _build_url_fallback(recommendations)

    try:
        return await _create_via_api(recommendations, title)
    except Exception as e:
        logger.error("Instacart API call failed: %s — falling back to URLs", e)
        return _build_url_fallback(recommendations)


async def _create_via_api(
    recommendations: list[FoodRecommendation],
    title: str,
) -> dict[str, Any]:
    """Call the Instacart Developer Platform API."""
    # Build line items from recommendations
    line_items = []
    for rec in recommendations:
        if rec.category == "supplement":
            continue  # Skip supplements — Instacart is for groceries

        line_item: dict[str, Any] = {
            "name": rec.name,
            "quantity": 1,
        }
        line_items.append(line_item)

    if not line_items:
        return _build_url_fallback(recommendations)

    # API request
    url = f"{settings.INSTACART_API_URL}/idp/v1/products/products_link"

    payload = {
        "title": title,
        "description": "Personalized grocery recommendations based on your lab report analysis by NutriScan AI.",
        "line_items": line_items,
        "link_type": "shopping_list",
    }

    headers = {
        "Authorization": f"Bearer {settings.INSTACART_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    # Extract the shopping list URL from response
    products_link_url = data.get("products_link_url", "")

    logger.info("Instacart shopping list created: %s", products_link_url)

    # Build cart items with the real API URL
    cart_items = []
    for rec in recommendations:
        cart_items.append({
            "name": rec.name,
            "emoji": rec.emoji,
            "nutrient": rec.nutrient,
            "amount": rec.amount,
            "category": rec.category,
            "instacart_url": products_link_url,  # All items link to the same list
        })

    return {
        "cart_items": cart_items,
        "shop_all_url": products_link_url,
        "api_used": True,
    }


# ---------------------------------------------------------------------------
# URL fallback — used when no API key is configured
# ---------------------------------------------------------------------------

def _build_url_fallback(
    recommendations: list[FoodRecommendation],
) -> dict[str, Any]:
    """Build Instacart search URLs (fallback when API is unavailable)."""
    cart_items = build_cart_urls(recommendations)
    shop_all_url = build_shop_all_url(recommendations)
    return {
        "cart_items": cart_items,
        "shop_all_url": shop_all_url,
        "api_used": False,
    }


def build_item_url(item_name: str) -> str:
    """Build an Instacart search URL for a single item."""
    return f"{INSTACART_SEARCH_BASE}/{quote_plus(item_name)}"


def build_cart_urls(
    recommendations: list[FoodRecommendation],
) -> list[dict]:
    """Build Instacart search URLs for each recommendation."""
    items = []
    for rec in recommendations:
        items.append({
            "name": rec.name,
            "emoji": rec.emoji,
            "nutrient": rec.nutrient,
            "amount": rec.amount,
            "category": rec.category,
            "instacart_url": build_item_url(rec.name),
        })
    return items


def build_shop_all_url(recommendations: list[FoodRecommendation]) -> str:
    """Build a combined Instacart search URL for all food items."""
    food_items = [r for r in recommendations if r.category == "food"]
    names = [r.name for r in food_items[:10]]
    query = " ".join(names)
    return f"{INSTACART_SEARCH_BASE}/{quote_plus(query)}"
