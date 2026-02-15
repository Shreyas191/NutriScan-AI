"""
Application configuration — loads environment variables via pydantic-settings.
"""

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

    # --- AI Provider (switch between "gemini" and "claude") ---
    AI_PROVIDER: str = "claude"

    # --- Anthropic (Claude) — kept for future hackathon use ---
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_SONNET_MODEL: str = "claude-3-5-haiku-20241022"
    CLAUDE_HAIKU_MODEL: str = "claude-3-haiku-20240307"

    # --- Google Gemini (free tier) ---
    GEMINI_API_KEY: str = ""
    GEMINI_FLASH_MODEL: str = "models/gemini-2.5-flash"
    GEMINI_PRO_MODEL: str = "models/gemini-2.5-flash"

    # --- Clerk ---
    CLERK_SECRET_KEY: str = ""
    CLERK_JWKS_URL: str = ""  # e.g. https://your-app.clerk.accounts.dev/.well-known/jwks.json
    CLERK_ISSUER: str = ""    # e.g. https://your-app.clerk.accounts.dev

    # --- Instacart Developer Platform ---
    INSTACART_API_KEY: str = ""
    INSTACART_API_URL: str = "https://connect.instacart.com"

    # --- Sentry ---
    SENTRY_DSN: str = ""

    # --- App ---
    ENVIRONMENT: str = "development"
    DEBUG: bool = True


settings = Settings()
