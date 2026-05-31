"""
Instacart cart automation via Playwright.

Session: loads cookies exported from real Chrome
(playwright_data/instacart_auth.json). To refresh after expiry:
    cd backend
    .venv/bin/python3.12 -c "
import browser_cookie3, json, os
cookies = []
for domain in ['instacart.com', '.instacart.com', 'www.instacart.com']:
    for c in browser_cookie3.chrome(domain_name=domain.lstrip('.')):
        cookies.append({'name':c.name,'value':c.value,'domain':c.domain,
            'path':c.path,'expires':c.expires or -1,'httpOnly':False,
            'secure':bool(c.secure),'sameSite':'Lax'})
os.makedirs('playwright_data', exist_ok=True)
with open('playwright_data/instacart_auth.json','w') as f:
    json.dump({'cookies':cookies,'origins':[]},f)
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

_AUTH_FILE = str(Path(__file__).parent.parent.parent / "playwright_data" / "instacart_auth.json")

_NAV_TIMEOUT  = 30_000
_ACT_TIMEOUT  = 10_000

# Instacart search selectors
_SEARCH_SELECTORS = [
    'input[data-testid="search-bar-input"]',
    'input[placeholder*="Search" i]',
    'input[aria-label*="Search" i]',
    '[data-testid="search-input"] input',
]

# Add to cart button selectors (search results page)
_ADD_SELECTORS = [
    'button[aria-label*="Add" i][aria-label*="cart" i]',
    'button[data-testid*="add" i]',
    'button:has-text("Add")',
    '[data-testid="add-to-cart-button"]',
]

# Login indicators
_LOGIN_INDICATORS = ["log in", "sign in", "create account", "login"]


async def _is_logged_in(page) -> bool:
    try:
        url = page.url.lower()
        if any(x in url for x in ["login", "signin", "sign_in"]):
            return False
        # Look for account/profile element
        for sel in ['[data-testid="account-menu"]', 'a[href*="/store/account"]', '[aria-label*="account" i]']:
            try:
                if await page.locator(sel).first.is_visible(timeout=3_000):
                    return True
            except Exception:
                pass
        return False
    except Exception:
        return False


async def _search_and_add(page, item_name: str, log_queue: asyncio.Queue) -> bool:
    log_queue.put_nowait(f"🔍 Searching: {item_name}")

    # Navigate back to store root between items so search bar is always fresh
    await page.goto("https://www.instacart.com/store", wait_until="domcontentloaded", timeout=_NAV_TIMEOUT)
    await asyncio.sleep(2)

    # Click search bar and type
    for sel in _SEARCH_SELECTORS:
        try:
            field = page.locator(sel).first
            if await field.is_visible(timeout=6_000):
                await field.click()
                await field.fill("")
                await field.type(item_name, delay=50)
                await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                break
        except Exception:
            continue
    else:
        log_queue.put_nowait(f"⚠️ Could not find search bar for: {item_name}")
        return False

    # Wait for results and click Add
    for sel in _ADD_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=_ACT_TIMEOUT):
                await btn.scroll_into_view_if_needed(timeout=3_000)
                await btn.click(timeout=_ACT_TIMEOUT)
                log_queue.put_nowait(f"✅ Added: {item_name}")
                await asyncio.sleep(1)
                return True
        except Exception:
            continue

    log_queue.put_nowait(f"⚠️ Skipped (button not found): {item_name}")
    return False


async def run_instacart_cart(items: list[str]) -> AsyncGenerator[str, None]:
    """
    Add items to an Instacart cart via Playwright.
    Loads session from playwright_data/instacart_auth.json.
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
                log_queue.put_nowait("❌ No session file at playwright_data/instacart_auth.json — export cookies first.")
                return

            with open(_AUTH_FILE) as f:
                storage_state = json.load(f)

            async with async_playwright() as pw:
                log_queue.put_nowait("🌐 Launching browser…")

                browser = await pw.chromium.launch(
                    headless=False,
                    channel="chrome",
                    slow_mo=60,
                    args=["--disable-blink-features=AutomationControlled"],
                    ignore_default_args=["--enable-automation"],
                )
                ctx = await browser.new_context(
                    storage_state=storage_state,
                    viewport={"width": 1400, "height": 900},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                )
                page = await ctx.new_page()
                await page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

                # Go straight to the store — cookies handle auth
                log_queue.put_nowait("🛒 Loading Instacart store…")
                await page.goto("https://www.instacart.com/store", wait_until="domcontentloaded", timeout=_NAV_TIMEOUT)
                await asyncio.sleep(3)

                # Only block if we're actually redirected to a login page
                if any(x in page.url.lower() for x in ["login", "signin", "sign_in"]):
                    log_queue.put_nowait("🔐 Please log in to Instacart in the browser window. Waiting up to 3 minutes…")
                    for _ in range(36):
                        await asyncio.sleep(5)
                        if not any(x in page.url.lower() for x in ["login", "signin"]):
                            log_queue.put_nowait("✅ Login detected!")
                            break
                    else:
                        log_queue.put_nowait("❌ Login timed out.")
                        await browser.close()
                        return
                else:
                    log_queue.put_nowait("✅ Session active.")

                log_queue.put_nowait(f"📋 Adding {len(items)} items to cart…")
                for item in items:
                    ok = await _search_and_add(page, item, log_queue)
                    if ok:
                        added += 1
                    else:
                        failed.append(item)

                await browser.close()

        except Exception as exc:
            logger.error("Instacart cart error: %s", exc, exc_info=True)
            log_queue.put_nowait(f"❌ Error: {exc}")
        finally:
            summary = f"✅ Done — {added}/{len(items)} items added to Instacart cart."
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
