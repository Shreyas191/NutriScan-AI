"""
Application configuration — loads environment variables via pydantic-settings.
"""

from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All env-based configuration for NutriScan AI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/nutriscan"

    # --- Anthropic (Claude) ---
    ANTHROPIC_API_KEY: str | None = None
    CLAUDE_SONNET_MODEL: str = "claude-3-5-haiku-20241022"
    CLAUDE_HAIKU_MODEL: str = "claude-3-haiku-20240307"

    # --- Cerebras (fast free LLM — best for browser automation) ---
    # Get free key at https://cloud.cerebras.ai
    CEREBRAS_API_KEY: str = ""

    # --- OpenRouter (free model fallback for browser automation) ---
    # Get free key at https://openrouter.ai
    OPENROUTER_API_KEY: str = ""

    # --- Browser-Use Cloud (paid, best model for browser automation) ---
    # Get key at https://cloud.browser-use.com/new-api-key
    BROWSER_USE_API_KEY: str = ""

    # --- Instacart Developer Platform ---
    INSTACART_API_KEY: str = ""
    INSTACART_API_URL: str = "https://connect.dev.instacart.tools"
    INSTACART_LOCATION: str = ""
    INSTACART_EMAIL: str = ""

    # --- Google Gemini (legacy, unused) ---
    GEMINI_API_KEY: str = ""

    # --- Groq (free LLM for analysis pipeline) ---
    GROQ_API_KEY: str = ""

    # --- Walmart ---
    WALMART_EMAIL: str | None = None
    WALMART_PASSWORD: str | None = None

    # --- Clerk ---
    CLERK_SECRET_KEY: str = ""
    CLERK_JWKS_URL: str = ""  # e.g. https://your-app.clerk.accounts.dev/.well-known/jwks.json
    CLERK_ISSUER: str = ""    # e.g. https://your-app.clerk.accounts.dev

    # --- Sentry ---
    SENTRY_DSN: str = ""

    # --- App ---
    ENVIRONMENT: str = "development"
    DEBUG: bool = True


settings = Settings()
