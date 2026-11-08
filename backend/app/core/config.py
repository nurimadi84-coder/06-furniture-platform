"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for MebelExpress API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "MebelExpress API"
    DATABASE_URL: str = "sqlite+aiosqlite:///./furniture.db"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    OPENAI_API_KEY: str = ""
    CORS_ORIGINS: str = "*"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
