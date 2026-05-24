from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="AI Agent Orchestration Dashboard API", min_length=1)
    app_version: str = Field(default="0.1.0", min_length=1)
    environment: str = Field(default="development", min_length=1)

    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout_seconds: float = 60.0

    database_url: str = Field(default="sqlite:///./orchestration.db", min_length=1)
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        str_strip_whitespace=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
