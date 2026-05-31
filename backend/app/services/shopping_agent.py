"""
Shopping Agent — orchestrates adding items to the user's Walmart cart
via the MCP Walmart server.

Replaces the previous browser-automation-based ShoppingAgent.
"""

import logging
from typing import AsyncGenerator

from app.config import settings

logger = logging.getLogger(__name__)


class ShoppingAgent:
    """
    Orchestrator for shopping tasks using MCP Walmart.
    Searches for products and adds them to the user's Walmart cart directly.
    """

    async def run_shopping_task(
        self,
        items: list[str],
    ) -> AsyncGenerator[str, None]:
        """
        Add items to the user's Walmart cart via MCP.
        Yields status logs for SSE streaming.
        """
        yield "🚀 Initializing Walmart MCP agent..."

        if not items:
            yield "⚠️ No items to shop for. Exiting."
            return

        from app.services.instacart_mcp import search_products, add_to_cart

        yield f"🛒 Adding {len(items)} items to your Walmart cart..."

        for item in items:
            yield f"🔍 Searching for: {item}"

            try:
                search_result = await search_products(item)

                if "error" in search_result:
                    yield f"⚠️ Search failed for {item}: {search_result['error']}"
                    continue

                products = search_result.get("products", [])
                if not products:
                    yield f"⚠️ Could not find {item} on Walmart"
                    continue

                product = products[0]
                product_id = product.get("id") or product.get("product_id", "")
                product_name = product.get("name", item)

                yield f"✅ Found: {product_name}. Adding to cart..."

                cart_result = await add_to_cart(product_id, quantity=1)

                if cart_result.get("success", True) and "error" not in cart_result:
                    yield f"🛒 Successfully added {product_name} to cart."
                else:
                    yield f"⚠️ Failed to add {item} to cart: {cart_result.get('error', 'Unknown error')}"

            except Exception as e:
                logger.error(f"Shopping task failed for {item}: {e}", exc_info=True)
                yield f"❌ Error adding {item}: {str(e)}"

        yield "✅ Shopping task completed."


# Singleton
shopping_agent = ShoppingAgent()
