"""
One-time Walmart login script.

Automates email + password entry using credentials from .env.
If Walmart sends an OTP, a browser window stays open so you can type it.
Session is saved to playwright_data/walmart_profile/ and reused by the backend.

Usage:
    cd backend
    .venv/bin/python3.12 scripts/walmart_login.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

WALMART_EMAIL = os.getenv("WALMART_EMAIL", "")
WALMART_PASSWORD = os.getenv("WALMART_PASSWORD", "")

PROFILE_DIR = str(Path(__file__).parent.parent / "playwright_data" / "walmart_profile")

LOGIN_URL = "https://www.walmart.com/account/login"


async def main():
    from playwright.async_api import async_playwright

    if not WALMART_EMAIL or not WALMART_PASSWORD:
        print("❌ WALMART_EMAIL or WALMART_PASSWORD not set in .env")
        sys.exit(1)

    print(f"📧 Email: {WALMART_EMAIL}")
    print(f"📁 Profile dir: {PROFILE_DIR}")
    os.makedirs(PROFILE_DIR, exist_ok=True)

    async with async_playwright() as pw:
        print("🌐 Opening Chrome…")
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            channel="chrome",
            slow_mo=80,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        page = await context.new_page()

        print("🛒 Navigating to Walmart login…")
        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(2)

        async def _try_fill(selectors: list[str], value: str, label: str) -> bool:
            for sel in selectors:
                try:
                    field = page.locator(sel).first
                    if await field.is_visible(timeout=4_000):
                        await field.click()
                        await field.fill(value)
                        print(f"✅ {label} filled.")
                        return True
                except Exception:
                    continue
            return False

        async def _try_click(selectors: list[str], label: str) -> bool:
            for sel in selectors:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=3_000):
                        await btn.click()
                        print(f"✅ {label} clicked.")
                        return True
                except Exception:
                    continue
            return False

        # Step 1 — fill email (Walmart identity.walmart.com uses name="email" or id="email")
        email_selectors = [
            'input[name="email"]',
            'input[id="email"]',
            'input[type="email"]',
            'input[placeholder*="email" i]',
            'input[autocomplete="email"]',
        ]
        filled = await _try_fill(email_selectors, WALMART_EMAIL, "Email")
        if not filled:
            print("⚠️  Could not fill email automatically — please type it in the browser window.")

        await asyncio.sleep(0.8)

        # Step 2 — click Continue/Next to advance to password step
        await _try_click([
            'button:has-text("Continue")',
            'button:has-text("Next")',
            'button[type="submit"]',
        ], "Continue")

        await asyncio.sleep(2)

        # Step 3 — fill password (may appear on second screen)
        pwd_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id="password"]',
            'input[autocomplete="current-password"]',
        ]
        filled = await _try_fill(pwd_selectors, WALMART_PASSWORD, "Password")
        if not filled:
            print("⚠️  Could not fill password automatically — please type it in the browser window.")

        await asyncio.sleep(0.8)

        # Step 4 — submit sign-in
        await _try_click([
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
            'button[type="submit"]',
            '[data-automation-id="signin-submit-btn"]',
        ], "Sign-in")

        # Wait for either: successful login OR OTP prompt
        print("\n⏳ Waiting for login to complete…")
        print("   ➡️  Complete any OTP / phone verification in the browser window.")
        print("   The script will detect login and exit automatically (up to 3 minutes).\n")

        for i in range(36):  # 36 × 5s = 3 minutes
            await asyncio.sleep(5)

            # Guard against navigation destroying the execution context
            try:
                current_url = page.url.lower()
            except Exception:
                current_url = ""
            try:
                title = (await page.title()).lower()
            except Exception:
                title = ""

            auth_urls = ["login", "signin", "otp", "verify", "2fa", "phoneverification", "identity.walmart.com"]
            on_auth_page = any(x in current_url for x in auth_urls)

            if current_url and not on_auth_page:
                print(f"✅ Login successful! (URL: {page.url})")
                break

            remaining = (36 - i - 1) * 5
            print(f"   Still waiting… {remaining}s remaining. Current: {current_url[:70]}")
        else:
            print("❌ Timed out waiting for login. Try again.")
            await context.close()
            return

        print("\n💾 Saving session to profile…")
        await context.close()
        print(f"✅ Session saved to: {PROFILE_DIR}")
        print("\n🎉 Done! The backend will now use this session for headless Walmart cart automation.")


if __name__ == "__main__":
    asyncio.run(main())
