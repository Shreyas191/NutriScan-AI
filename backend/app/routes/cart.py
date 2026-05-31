"""
Cart API — autonomous shopping agent endpoint.

POST /api/cart/auto-shop
  Accepts a list of items + retailer, streams SSE logs as Playwright
  adds each item to the Walmart cart directly (no LLM — fast).
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cart", tags=["Cart"])


_SUPPORTED_RETAILERS = ("instacart", "walmart")


class AutoShopRequest(BaseModel):
    items: list[str]
    retailer: str = "instacart"


@router.post("/auto-shop")
async def auto_shop(req: AutoShopRequest):
    """
    Add items to a cart via Playwright browser automation.
    Streams Server-Sent Events with progress log lines.

    Supported retailers: instacart (default), walmart
    Session cookies must be exported from Chrome first.
    """
    if not req.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No items provided",
        )

    if req.retailer not in _SUPPORTED_RETAILERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Retailer '{req.retailer}' not supported. Use: {', '.join(_SUPPORTED_RETAILERS)}",
        )

    async def event_stream():
        if req.retailer == "instacart":
            from app.agents.instacart_cart import run_instacart_cart
            runner = run_instacart_cart(req.items)
            label = "Instacart"
        else:
            from app.agents.playwright_cart import run_playwright_cart
            runner = run_playwright_cart(req.items)
            label = "Walmart"

        yield f"data: {json.dumps({'log': f'Starting {label} cart automation for {len(req.items)} items…'})}\n\n"

        try:
            async for log_line in runner:
                yield f"data: {json.dumps({'log': log_line})}\n\n"

            yield f"data: {json.dumps({'status': 'done'})}\n\n"

        except Exception as exc:
            logger.error("auto_shop stream error: %s", exc, exc_info=True)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
