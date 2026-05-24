from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="AI Agent Orchestration Dashboard API", min_length=1)
    app_version: str = Field(default="0.1.0", min_length=1)
    environment: str = Field(default="development", min_length=1)

    openrouter_api_key: str | None = None
    openrouter_model: str = Field(default="openai/gpt-4o-mini", min_length=1)
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", min_length=1)
    openrouter_timeout_seconds: float = Field(default=60.0, gt=0)

    database_url: str = Field(default="sqlite:///./orchestration.db", min_length=1)
    cors_allowed_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        min_length=1,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        str_strip_whitespace=True,
    )

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(cls, origins: list[str]) -> list[str]:
        """Reject blank CORS origins."""
        if any(not origin.strip() for origin in origins):
            raise ValueError("cors_allowed_origins must not include blank origins")
        return [origin.strip() for origin in origins]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
