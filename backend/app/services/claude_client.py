"""
Shared Anthropic Claude client for all AI services.
"""

from anthropic import Anthropic

from app.config import settings

# Singleton client — initialised once, reused across services.
_client: Anthropic | None = None


def get_client() -> Anthropic:
    """Return a lazily-initialised Anthropic client."""
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


# Convenient model name aliases
HAIKU = settings.CLAUDE_HAIKU_MODEL
SONNET = settings.CLAUDE_SONNET_MODEL
