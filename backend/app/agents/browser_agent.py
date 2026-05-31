"""
Browser Agent — autonomous Walmart cart automation via browser-use.

LLM priority (first key present wins):
  1. ChatCerebras    — llama-3.3-70b, fast + free, no daily cap  (CEREBRAS_API_KEY)
  2. ChatOpenRouter  — llama-3.3-70b:free, unlimited free tier    (OPENROUTER_API_KEY)
  3. ChatGroq        — llama-3.3-70b-versatile, 100k TPD free     (GROQ_API_KEY)
  4. ChatBrowserUse  — purpose-built model, paid                   (BROWSER_USE_API_KEY)

Session: persists Walmart login in backend/browser_data/ — OTP only needed once.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

_BROWSER_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "browser_data")
)

# Chrome lock files that prevent reuse of a profile after an unclean shutdown
_CHROME_LOCK_FILES = ("SingletonLock", "SingletonCookie", "SingletonSocket")


def _clear_chrome_locks(profile_dir: str) -> None:
    for name in _CHROME_LOCK_FILES:
        path = os.path.join(profile_dir, name)
        try:
            os.remove(path)
            logger.info("Removed stale Chrome lock: %s", path)
        except FileNotFoundError:
            pass


def _build_task(items: list[str]) -> str:
    items_list = "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
    return f"""You are adding grocery items to a Walmart shopping cart.

IMPORTANT: Do NOT call done until ALL items have been added to the cart.

Steps to follow:
1. Go to https://www.walmart.com
2. If not logged in: click Sign In, enter credentials. If OTP is requested, wait 60 seconds for the user to enter it.
3. For EACH item in the list below:
   a. Click the search bar
   b. Type the item name and press Enter
   c. Click "Add to cart" on the most relevant result
   d. Confirm the item was added
4. After ALL items are added, call done with a summary.

Items to add to cart:
{items_list}

Do not skip any items. Add them one by one."""


def _build_llm_chain(
    groq_api_key: str,
    cerebras_api_key: str | None,
    openrouter_api_key: str | None,
    browser_use_api_key: str | None,
) -> list:
    """
    Build an ordered list of (label, llm) pairs to try.
    First key present wins; Groq is always last-resort since it has a daily cap.
    """
    chain = []

    if cerebras_api_key:
        from browser_use.llm.cerebras.chat import ChatCerebras
        # qwen-3-235b is the largest accessible model on the free tier
        chain.append((
            "Cerebras qwen-3-235b",
            ChatCerebras(model="qwen-3-235b-a22b-instruct-2507", api_key=cerebras_api_key),
        ))
        chain.append((
            "Cerebras llama3.1-8b",
            ChatCerebras(model="llama3.1-8b", api_key=cerebras_api_key),
        ))

    if openrouter_api_key:
        from browser_use.llm.openrouter.chat import ChatOpenRouter
        chain.append((
            "OpenRouter llama-3.3-70b:free",
            ChatOpenRouter(
                model="meta-llama/llama-3.3-70b-instruct:free",
                api_key=openrouter_api_key,
            ),
        ))

    # Groq non-thinking models (no reasoning tokens — safe for browser-use)
    if groq_api_key:
        from browser_use.llm.groq.chat import ChatGroq
        for model in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"):
            chain.append((f"Groq {model}", ChatGroq(model=model, api_key=groq_api_key)))

    if browser_use_api_key:
        from browser_use import ChatBrowserUse
        chain.append(("ChatBrowserUse", ChatBrowserUse(api_key=browser_use_api_key)))

    return chain


async def run_browser_agent(
    retailer: str,
    items: list[str],
    groq_api_key: str,
    cerebras_api_key: str | None = None,
    openrouter_api_key: str | None = None,
    browser_use_api_key: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Launch a browser-use Agent to add items to a Walmart cart.
    Yields plain-text log lines for SSE streaming.
    """
    from browser_use import Agent, Browser, Tools, ActionResult

    if retailer != "walmart":
        yield f"Unsupported retailer: {retailer}"
        return

    os.makedirs(_BROWSER_DATA_DIR, exist_ok=True)

    log_queue: asyncio.Queue[str | None] = asyncio.Queue()

    # Custom tool: pauses so user can enter OTP in the visible browser
    tools = Tools()

    @tools.action("Wait for the user to complete OTP or manual sign-in in the browser window")
    async def wait_for_otp(seconds: int = 60) -> ActionResult:
        log_queue.put_nowait(f"⏳ Waiting {seconds}s — please enter your OTP in the browser window…")
        await asyncio.sleep(seconds)
        return ActionResult(extracted_content="Waited for user to complete authentication.")

    async def on_step_end(agent) -> None:
        """Called after each step — use Agent state to log progress."""
        try:
            output = agent.state.last_model_output
            if output and output.next_goal:
                step = agent.state.n_steps
                log_queue.put_nowait(f"Step {step}: {output.next_goal}")
        except Exception:
            pass

    async def _run() -> None:
        llm_chain = _build_llm_chain(
            groq_api_key, cerebras_api_key, openrouter_api_key, browser_use_api_key
        )
        if not llm_chain:
            log_queue.put_nowait("❌ No LLM API keys configured.")
            return

        for label, llm in llm_chain:
            log_queue.put_nowait(f"🤖 Using {label}…")
            try:
                _clear_chrome_locks(_BROWSER_DATA_DIR)
                browser = Browser(
                    headless=False,
                    user_data_dir=_BROWSER_DATA_DIR,
                )
                agent = Agent(
                    task=_build_task(items),
                    llm=llm,
                    browser=browser,
                    tools=tools,
                    use_vision=False,    # Cerebras/Groq models are text-only
                    use_thinking=False,  # Disable reasoning tokens (not supported by these models)
                    max_failures=5,
                    step_timeout=120,
                )
                log_queue.put_nowait(
                    "🌐 Browser opening — if Walmart asks for OTP, enter it in the browser window."
                )
                history = await agent.run(max_steps=60, on_step_end=on_step_end)

                if history.is_successful():
                    result = history.final_result() or "all items added"
                    log_queue.put_nowait(f"✅ Done: {result}")
                    return
                else:
                    errors = [e for e in (history.errors() or []) if e]
                    err_str = str(errors[-1]) if errors else ""
                    _SKIP_KEYWORDS = ("rate limit", "free tier", "upgrade", "429", "413", "quota",
                                      "404", "does not exist", "decommissioned", "not found")
                    if any(k in err_str.lower() for k in _SKIP_KEYWORDS):
                        log_queue.put_nowait(f"⚠️ {label} limit hit — trying next model…")
                        continue
                    log_queue.put_nowait(f"⚠️ Agent finished: {err_str or 'no result'}")
                    return

            except Exception as exc:
                exc_str = str(exc).lower()
                _SKIP_KEYWORDS = ("rate limit", "free tier", "upgrade", "429", "413", "quota")
                if any(k in exc_str for k in _SKIP_KEYWORDS):
                    log_queue.put_nowait(f"⚠️ {label} limit — trying next model…")
                    continue
                logger.error("Browser agent error: %s", exc, exc_info=True)
                log_queue.put_nowait(f"❌ Error: {exc}")
                return

        log_queue.put_nowait("❌ All models exhausted — please try again later or add items manually.")

    async def _run_wrapper() -> None:
        try:
            await _run()
        finally:
            log_queue.put_nowait(None)

    agent_task = asyncio.create_task(_run_wrapper())

    try:
        while True:
            log = await log_queue.get()
            if log is None:
                break
            yield log
    finally:
        if not agent_task.done():
            agent_task.cancel()
            try:
                await agent_task
            except asyncio.CancelledError:
                pass
