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
