"""
Shared Google Gemini client for all AI services.

Uses the modern google-genai SDK (replaces deprecated google-generativeai).
"""

from google import genai

from app.config import settings

# Create a shared client instance
_client: genai.Client | None = None

# Convenient model name aliases
FLASH = settings.GEMINI_FLASH_MODEL
PRO = settings.GEMINI_PRO_MODEL


def get_client() -> genai.Client:
    """Return the shared Gemini client (lazy init)."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client
