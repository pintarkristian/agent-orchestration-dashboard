"""Shared FastAPI dependency providers."""

from app.services.openrouter_client import OpenRouterClient


def get_openrouter_client() -> OpenRouterClient:
    """Create the OpenRouter client dependency."""
    return OpenRouterClient()


__all__ = ["get_openrouter_client"]
