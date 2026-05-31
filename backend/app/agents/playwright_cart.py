"""
Walmart cart automation via direct Playwright — no LLM, no rate limits.

Session persistence: loads cookies exported from the user's real Chrome browser
(playwright_data/walmart_auth.json). To refresh the session after expiry, run:
    cd backend && .venv/bin/python3.12 -m pip install -q browser-cookie3
    .venv/bin/python3.12 -c "
import browser_cookie3, json, os
cookies = []
for domain in ['.walmart.com', 'identity.walmart.com', 'www.walmart.com']:
    for c in browser_cookie3.chrome(domain_name=domain.lstrip('.')):
        cookies.append({'name':c.name,'value':c.value,'domain':c.domain,
            'path':c.path,'expires':c.expires or -1,'httpOnly':False,
            'secure':bool(c.secure),'sameSite':'Lax'})
os.makedirs('playwright_data', exist_ok=True)
with open('playwright_data/walmart_auth.json','w') as f: json.dump({'cookies':cookies,'origins':[]},f)
print(f'Saved {len(cookies)} cookies')
"
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

_AUTH_FILE = str(Path(__file__).parent.parent.parent / "playwright_data" / "walmart_auth.json")

_NAV_TIMEOUT_MS = 30_000
_ACTION_TIMEOUT_MS = 10_000

_ADD_TO_CART_SELECTORS = [
    '[data-automation-id="add-to-cart-section"]',
    'button[aria-label*="Add to cart" i]',
    'button:has-text("Add to cart")',
    '[data-testid*="add-to-cart" i]',
]

_DISMISS_SELECTORS = [
    'button[aria-label*="close" i]',
    'button:has-text("Continue shopping")',
    'button:has-text("Close")',
]

_LOGIN_INDICATORS = [
    "sign in",
    "log in",
    "signin",
    "create an account",
]


async def _dismiss_popup(page) -> None:
    for sel in _DISMISS_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=2_000):
                await btn.click(timeout=3_000)
                return
        except Exception:
            pass


async def _is_logged_in(page) -> bool:
    """Check if the current Walmart page shows a logged-in state."""
    try:
        title = (await page.title()).lower()
        url = page.url.lower()

        if any(ind in title for ind in _LOGIN_INDICATORS):
            return False
        if any(ind in url for ind in ["signin", "login", "account/login"]):
            return False

        # Check for account-related UI element
        account_btn = page.locator('[aria-label*="Account" i], [data-automation-id*="account" i]').first
        return await account_btn.is_visible(timeout=3_000)
    except Exception:
        return False


async def _add_item(page, item_name: str, log_queue: asyncio.Queue) -> bool:
    url = f"https://www.walmart.com/search?q={quote_plus(item_name)}"
    log_queue.put_nowait(f"🔍 Searching: {item_name}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
    except Exception as exc:
        log_queue.put_nowait(f"⚠️ Page load failed for {item_name}: {exc}")
        return False

    await asyncio.sleep(2)

    for sel in _ADD_TO_CART_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=_ACTION_TIMEOUT_MS):
                await btn.scroll_into_view_if_needed(timeout=3_000)
                await btn.click(timeout=_ACTION_TIMEOUT_MS)
                log_queue.put_nowait(f"✅ Added: {item_name}")
                await asyncio.sleep(1.5)
                await _dismiss_popup(page)
                return True
        except Exception:
            continue

    log_queue.put_nowait(f"⚠️ Skipped (button not found): {item_name}")
    return False


async def run_playwright_cart(items: list[str]) -> AsyncGenerator[str, None]:
    """
    Add items to a Walmart cart via Playwright.

    Loads the Walmart session from playwright_data/walmart_auth.json
    (cookies exported from real Chrome). Runs fully headless — no browser window.
    Yields SSE log lines.
    """
    from playwright.async_api import async_playwright

    log_queue: asyncio.Queue[str | None] = asyncio.Queue()
    added = 0
    failed: list[str] = []

    async def _run() -> None:
        nonlocal added
        try:
            if not os.path.exists(_AUTH_FILE):
                log_queue.put_nowait("❌ No session file found at playwright_data/walmart_auth.json — please export cookies first.")
                return

            with open(_AUTH_FILE) as f:
                storage_state = json.load(f)

            async with async_playwright() as pw:
                log_queue.put_nowait("🌐 Launching headless Chrome…")
                browser = await pw.chromium.launch(
                    headless=True,
                    channel="chrome",
                    slow_mo=30,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(
                    storage_state=storage_state,
                    viewport={"width": 1400, "height": 900},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                )
                page = await context.new_page()

                log_queue.put_nowait("🛒 Verifying Walmart session…")
                await page.goto("https://www.walmart.com", wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
                await asyncio.sleep(2)

                if not await _is_logged_in(page):
                    log_queue.put_nowait("⚠️ Session expired — please re-export cookies from Chrome and try again.")
                    await browser.close()
                    return

                log_queue.put_nowait("✅ Walmart session active.")
                log_queue.put_nowait(f"📋 Adding {len(items)} items to cart…")

                for item in items:
                    ok = await _add_item(page, item, log_queue)
                    if ok:
                        added += 1
                    else:
                        failed.append(item)

                await browser.close()

        except Exception as exc:
            logger.error("Playwright cart error: %s", exc, exc_info=True)
            log_queue.put_nowait(f"❌ Error: {exc}")
        finally:
            summary = f"✅ Done — {added}/{len(items)} items added to cart."
            if failed:
                summary += f" Skipped: {', '.join(failed)}"
            log_queue.put_nowait(summary)
            log_queue.put_nowait(None)

    task = asyncio.create_task(_run())
    try:
        while True:
            line = await log_queue.get()
            if line is None:
                break
            yield line
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
