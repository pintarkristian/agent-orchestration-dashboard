from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class OpenRouterClientError(RuntimeError):
    """Base exception for OpenRouter client errors."""


class MissingOpenRouterAPIKeyError(OpenRouterClientError):
    """Raised when OPENROUTER_API_KEY is not configured."""


class OpenRouterHTTPError(OpenRouterClientError):
    """Raised when OpenRouter returns a non-success HTTP response."""


class OpenRouterInvalidResponseError(OpenRouterClientError):
    """Raised when OpenRouter returns an unexpected response payload."""


class OpenRouterTimeoutError(OpenRouterClientError):
    """Raised when the OpenRouter request times out."""


class OpenRouterClient:
    """Async client for OpenRouter chat completion requests."""

    _MAX_ERROR_BODY_LENGTH = 500

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | httpx.BaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        configured_api_key = api_key if api_key is not None else settings.openrouter_api_key
        self.api_key = configured_api_key.strip() if configured_api_key is not None else None
        self.model = self._normalize_required_text(
            model if model is not None else settings.openrouter_model,
            field_name="model",
        )
        self.base_url = self._normalize_base_url(
            base_url if base_url is not None else settings.openrouter_base_url,
        )
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.openrouter_timeout_seconds
        )
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")
        self._transport = transport

    def build_headers(self) -> dict[str, str]:
        """Build default headers for OpenRouter requests."""
        if not self.api_key:
            raise MissingOpenRouterAPIKeyError("OPENROUTER_API_KEY is required to call OpenRouter.")

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_async_client(self) -> httpx.AsyncClient:
        """Create an async HTTP client configured for OpenRouter."""
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.build_headers(),
            timeout=httpx.Timeout(self.timeout_seconds),
            transport=self._transport,
        )

    @staticmethod
    def _normalize_required_text(value: str, *, field_name: str) -> str:
        """Normalize a required text setting and fail fast when it is blank."""
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank.")
        return normalized

    @staticmethod
    def _normalize_base_url(value: str) -> str:
        """Normalize and validate the OpenRouter base URL."""
        normalized = OpenRouterClient._normalize_required_text(value, field_name="base_url").rstrip(
            "/"
        )
        if not normalized:
            raise ValueError("base_url must not be blank.")

        parsed = httpx.URL(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.host:
            raise ValueError("base_url must be an absolute HTTP(S) URL.")

        return normalized

    @classmethod
    def _truncate_error_body(cls, response_text: str) -> str:
        """Keep provider error bodies readable without letting them dominate logs."""
        if len(response_text) <= cls._MAX_ERROR_BODY_LENGTH:
            return response_text
        return f"{response_text[: cls._MAX_ERROR_BODY_LENGTH].rstrip()}... [truncated]"

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a chat completion using OpenRouter.

        Args:
            system_prompt: Instructions that define the assistant behavior.
            user_prompt: The user-facing prompt to complete.

        Returns:
            The first assistant message content returned by OpenRouter.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            async with self.create_async_client() as client:
                response = await client.post("/chat/completions", json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise OpenRouterTimeoutError("OpenRouter request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            response_text = self._truncate_error_body(exc.response.text)
            raise OpenRouterHTTPError(
                f"OpenRouter returned HTTP {exc.response.status_code}: {response_text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise OpenRouterHTTPError(f"OpenRouter request failed: {exc}") from exc

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise OpenRouterInvalidResponseError(
                "OpenRouter returned an invalid chat completion response."
            ) from exc

        if not isinstance(content, str):
            raise OpenRouterInvalidResponseError(
                "OpenRouter response did not include assistant text content."
            )

        normalized_content = content.strip()
        if not normalized_content:
            raise OpenRouterInvalidResponseError(
                "OpenRouter response did not include assistant text content."
            )

        return normalized_content
