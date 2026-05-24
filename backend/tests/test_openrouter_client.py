import json

import httpx
import pytest
from app.services.openrouter_client import (
    MissingOpenRouterAPIKeyError,
    OpenRouterClient,
    OpenRouterHTTPError,
    OpenRouterInvalidResponseError,
    OpenRouterTimeoutError,
)


@pytest.mark.asyncio
async def test_generate_completion_returns_assistant_content() -> None:
    captured_requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Generated orchestration plan.",
                        }
                    }
                ]
            },
        )

    client = OpenRouterClient(
        api_key="test-api-key",
        model="test/model",
        base_url="https://openrouter.ai/api/v1",
        timeout_seconds=5,
        transport=httpx.MockTransport(handler),
    )

    result = await client.generate_completion(
        system_prompt="You are a planner.",
        user_prompt="Create a plan.",
    )

    assert result == "Generated orchestration plan."
    assert len(captured_requests) == 1

    request = captured_requests[0]
    assert request.method == "POST"
    assert request.url.path == "/api/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer test-api-key"

    payload = json.loads(request.content.decode("utf-8"))
    assert payload["model"] == "test/model"
    assert payload["messages"] == [
        {"role": "system", "content": "You are a planner."},
        {"role": "user", "content": "Create a plan."},
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("api_key", ["", "   "])
async def test_generate_completion_requires_api_key(api_key: str) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json={})

    client = OpenRouterClient(
        api_key=api_key,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(MissingOpenRouterAPIKeyError):
        await client.generate_completion("system", "user")


@pytest.mark.asyncio
async def test_generate_completion_strips_api_key_whitespace() -> None:
    captured_requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "Generated plan"}}]},
        )

    client = OpenRouterClient(
        api_key="  test-api-key  ",
        transport=httpx.MockTransport(handler),
    )

    await client.generate_completion("system", "user")

    assert captured_requests[0].headers["Authorization"] == "Bearer test-api-key"


@pytest.mark.asyncio
async def test_generate_completion_strips_response_content_whitespace() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "\n  Generated plan.  \n"}}]},
        )

    client = OpenRouterClient(
        api_key="test-api-key",
        transport=httpx.MockTransport(handler),
    )

    result = await client.generate_completion("system", "user")

    assert result == "Generated plan."


@pytest.mark.parametrize("timeout_seconds", [0, -1])
def test_openrouter_client_rejects_non_positive_timeout(timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="timeout_seconds must be greater than 0"):
        OpenRouterClient(api_key="test-api-key", timeout_seconds=timeout_seconds)


def test_openrouter_client_normalizes_model_and_base_url() -> None:
    client = OpenRouterClient(
        api_key="test-api-key",
        model="  test/model  ",
        base_url="  https://openrouter.ai/api/v1/  ",
    )

    assert client.model == "test/model"
    assert client.base_url == "https://openrouter.ai/api/v1"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"model": ""}, "model must not be blank"),
        ({"model": "   "}, "model must not be blank"),
        ({"base_url": ""}, "base_url must not be blank"),
        ({"base_url": "   "}, "base_url must not be blank"),
        ({"base_url": "/"}, "base_url must not be blank"),
        ({"base_url": "openrouter.ai/api/v1"}, "base_url must be an absolute HTTP"),
        ({"base_url": "/api/v1"}, "base_url must be an absolute HTTP"),
        ({"base_url": "ftp://openrouter.ai/api/v1"}, "base_url must be an absolute HTTP"),
    ],
)
def test_openrouter_client_rejects_blank_text_configuration(
    kwargs: dict[str, str],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        OpenRouterClient(api_key="test-api-key", **kwargs)


@pytest.mark.asyncio
async def test_generate_completion_wraps_http_status_errors() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=429, json={"error": "rate limited"})

    client = OpenRouterClient(
        api_key="test-api-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(OpenRouterHTTPError, match="HTTP 429"):
        await client.generate_completion("system", "user")


@pytest.mark.asyncio
async def test_generate_completion_wraps_timeout_errors() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("request timed out")

    client = OpenRouterClient(
        api_key="test-api-key",
        timeout_seconds=0.01,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(OpenRouterTimeoutError):
        await client.generate_completion("system", "user")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response_payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": ""}}]},
        {"choices": [{"message": {"content": None}}]},
    ],
)
async def test_generate_completion_rejects_invalid_response_format(
    response_payload: dict,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json=response_payload)

    client = OpenRouterClient(
        api_key="test-api-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(OpenRouterInvalidResponseError):
        await client.generate_completion("system", "user")
