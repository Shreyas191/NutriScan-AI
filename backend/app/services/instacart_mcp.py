"""
Instacart MCP Integration — uses the @striderlabs/mcp-instacart MCP server
to search products and add items to a user's Instacart cart directly.

The MCP server is spawned as a subprocess via `npx @striderlabs/mcp-instacart`
and communicates over stdio using the Model Context Protocol.

Requires:
  - Node.js / npx installed on the host
  - INSTACART_EMAIL and INSTACART_PASSWORD in .env
  - pip install mcp
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


async def _call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Spawn the MCP Instacart server and call a single tool.

    Uses the `mcp` Python SDK to communicate over stdio.
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    # Build environment for the MCP subprocess
    env = {**os.environ}
    if settings.INSTACART_EMAIL:
        env["INSTACART_EMAIL"] = settings.INSTACART_EMAIL
    if settings.INSTACART_PASSWORD:
        env["INSTACART_PASSWORD"] = settings.INSTACART_PASSWORD

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@striderlabs/mcp-instacart"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(tool_name, arguments=arguments)

            # Extract text content from the result
            if result.content:
                for block in result.content:
                    if hasattr(block, "text"):
                        try:
                            return json.loads(block.text)
                        except json.JSONDecodeError:
                            return {"raw_text": block.text}

            return {"success": True}


async def search_products(query: str, location: str | None = None) -> dict[str, Any]:
    """Search Instacart for products matching a query."""
    args: dict[str, Any] = {"query": query}
    if location or settings.INSTACART_LOCATION:
        args["location"] = location or settings.INSTACART_LOCATION

    try:
        return await _call_mcp_tool("search_products", args)
    except Exception as e:
        logger.error("MCP search_products failed: %s", e)
        return {"error": str(e), "products": []}


async def add_to_cart(
    product_id: str,
    quantity: int = 1,
    special_instructions: str | None = None,
) -> dict[str, Any]:
    """Add a product to the user's Instacart cart."""
    args: dict[str, Any] = {
        "product_id": product_id,
        "quantity": quantity,
    }
    if special_instructions:
        args["special_instructions"] = special_instructions

    try:
        return await _call_mcp_tool("add_to_cart", args)
    except Exception as e:
        logger.error("MCP add_to_cart failed: %s", e)
        return {"error": str(e), "success": False}


async def add_recommendations_to_cart(
    items: list[str],
    location: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search for and add a list of food items to the Instacart cart.

    For each item:
      1. Search for it on Instacart
      2. Pick the first result
      3. Add it to cart

    Returns a list of results per item.
    """
    results = []
    loc = location or settings.INSTACART_LOCATION

    for item_name in items:
        item_result = {"name": item_name, "status": "pending"}

        try:
            # Step 1: Search
            search_result = await search_products(item_name, loc)

            if "error" in search_result:
                item_result["status"] = "search_failed"
                item_result["error"] = search_result["error"]
                results.append(item_result)
                continue

            # Step 2: Pick first product
            products = search_result.get("products", [])
            if not products:
                item_result["status"] = "not_found"
                results.append(item_result)
                continue

            product = products[0]
            product_id = product.get("id") or product.get("product_id", "")

            # Step 3: Add to cart
            cart_result = await add_to_cart(product_id, quantity=1)

            if cart_result.get("success", True) and "error" not in cart_result:
                item_result["status"] = "added"
                item_result["product"] = product.get("name", item_name)
            else:
                item_result["status"] = "add_failed"
                item_result["error"] = cart_result.get("error", "Unknown error")

        except Exception as e:
            item_result["status"] = "error"
            item_result["error"] = str(e)

        results.append(item_result)

    return results
