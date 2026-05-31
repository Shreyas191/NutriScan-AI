"""
LLM client — Groq (free tier) for NutriScan AI analysis pipeline.

Model lists contain only LIVE models as of 2026-04.
Decommissioned: llama-3.1-70b-versatile, llama3-70b-8192, gemma2-9b-it, llama-3.2-3b-preview
"""

from __future__ import annotations

import logging

from groq import AsyncGroq, APIStatusError

from app.config import settings

logger = logging.getLogger(__name__)

# Models verified to support tool/function calling on Groq (live as of 2026-04)
_TOOL_MODELS = [
    "llama-3.3-70b-versatile",                   # best quality; 100k TPD
    "openai/gpt-oss-20b",                         # no reasoning tokens; fresh quota
    "openai/gpt-oss-120b",                        # largest; fresh quota
    "meta-llama/llama-4-scout-17b-16e-instruct",  # thinking model — strip reasoning
    "llama-3.1-8b-instant",                       # last resort; small context (6k tokens)
]

# Models for plain JSON completions (wider net, no tool calling required)
_TEXT_MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "openai/gpt-oss-120b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]

_client: AsyncGroq | None = None
_tool_ref = ["llama-3.3-70b-versatile"]
_text_ref = ["llama-3.3-70b-versatile"]


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client


def get_model() -> str:
    return _tool_ref[0]


def _is_skippable(exc: APIStatusError) -> bool:
    msg = str(exc).lower()
    return (
        exc.status_code in (429, 413)
        or "decommissioned" in msg
        or "tool_use_failed" in msg
        or ("failed_generation" in msg and exc.status_code == 400)
    )


def _trim_messages(messages: list, max_tokens: int = 4000) -> list:
    """
    Rough token trimmer: keep system message + last N messages so the
    conversation fits within max_tokens (estimated at ~4 chars/token).
    """
    char_budget = max_tokens * 4
    system = [m for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]

    # Walk backwards until we fit
    kept = []
    used = sum(len(str(m)) for m in system)
    for m in reversed(rest):
        size = len(str(m))
        if used + size > char_budget and kept:
            break
        kept.insert(0, m)
        used += size

    return system + kept


async def _call_with_fallback(
    model_list: list[str],
    active_ref: list[str],
    **kwargs,
) -> object:
    client = get_client()
    start = model_list.index(active_ref[0]) if active_ref[0] in model_list else 0
    ordered = model_list[start:] + model_list[:start]

    last_exc: Exception | None = None
    for model in ordered:
        call_kwargs = dict(kwargs)

        # For small-context models, trim the message history so we don't 413
        if model == "llama-3.1-8b-instant" and "messages" in call_kwargs:
            call_kwargs["messages"] = _trim_messages(call_kwargs["messages"], max_tokens=4000)
            call_kwargs["max_tokens"] = min(call_kwargs.get("max_tokens", 1024), 512)

        try:
            response = await client.chat.completions.create(model=model, **call_kwargs)
            if model != active_ref[0]:
                logger.info("Active model → %s", model)
                active_ref[0] = model
            return response
        except APIStatusError as exc:
            if _is_skippable(exc):
                logger.warning("Model %s skipped (HTTP %s): %s",
                               model, exc.status_code, str(exc)[:120])
                last_exc = exc
                next_idx = (model_list.index(model) + 1) % len(model_list)
                active_ref[0] = model_list[next_idx]
                continue
            raise
        except Exception:
            raise

    raise RuntimeError(f"All models exhausted. Last error: {last_exc}")


async def chat_with_fallback(**kwargs) -> object:
    """Plain JSON completion — no tool calling required."""
    return await _call_with_fallback(_TEXT_MODELS, _text_ref, **kwargs)


async def tool_chat_with_fallback(**kwargs) -> object:
    """Tool-calling completion — only models that support function calling."""
    return await _call_with_fallback(_TOOL_MODELS, _tool_ref, **kwargs)
