import pytest
from app.agents.base_agent import BaseAgent
from app.agents.planner_agent import PlannerAgent
from app.api.routes.agents import get_openrouter_client
from app.main import app
from app.models.enums import AgentRole, WorkflowStatus
from fastapi.testclient import TestClient


class MockOpenRouterClient:
    def __init__(self, response: str = "1. Analyze request\n2. Create tasks") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.response


class FailingOpenRouterClient:
    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("OpenRouter failed")


@pytest.mark.asyncio
async def test_base_agent_run_returns_completed_result() -> None:
    client = MockOpenRouterClient(response="Generated plan")
    agent = BaseAgent(
        role=AgentRole.PLANNER,
        name="Test Planner",
        description="Test planner agent.",
        system_prompt="You are a planner.",
        openrouter_client=client,
    )

    result = await agent.run("Create a project structure")

    assert result.role == AgentRole.PLANNER
    assert result.input == "Create a project structure"
    assert result.output == "Generated plan"
    assert result.status == WorkflowStatus.COMPLETED
    assert result.error is None
    assert result.started_at is not None
    assert result.completed_at is not None
    assert result.duration_ms is not None
    assert result.duration_ms >= 0
    assert client.calls == [("You are a planner.", "Create a project structure")]


@pytest.mark.asyncio
async def test_base_agent_run_returns_failed_result_on_client_error() -> None:
    agent = BaseAgent(
        role=AgentRole.PLANNER,
        name="Test Planner",
        description="Test planner agent.",
        system_prompt="You are a planner.",
        openrouter_client=FailingOpenRouterClient(),
    )

    result = await agent.run("Create a project structure")

    assert result.role == AgentRole.PLANNER
    assert result.input == "Create a project structure"
    assert result.output is None
    assert result.status == WorkflowStatus.FAILED
    assert result.error == "OpenRouter failed"
    assert result.started_at is not None
    assert result.completed_at is not None
    assert result.duration_ms is not None
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_planner_agent_uses_planner_role_and_prompt() -> None:
    client = MockOpenRouterClient(response="1. First task\n2. Second task")
    agent = PlannerAgent(openrouter_client=client)

    result = await agent.run("Build an AI dashboard")

    assert agent.role == AgentRole.PLANNER
    assert agent.name == "Planner Agent"
    assert "break" in agent.system_prompt.lower()
    assert result.status == WorkflowStatus.COMPLETED
    assert result.output == "1. First task\n2. Second task"
    assert client.calls[0][1] == "Build an AI dashboard"


def test_run_planner_endpoint_returns_agent_execution_result() -> None:
    mock_client = MockOpenRouterClient(response="1. Define backend\n2. Define frontend")
    app.dependency_overrides[get_openrouter_client] = lambda: mock_client

    try:
        client = TestClient(app)
        response = client.post(
            "/api/agents/planner/run",
            json={"task": "Create an AI agent orchestration dashboard"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()
    assert data["role"] == "planner"
    assert data["input"] == "Create an AI agent orchestration dashboard"
    assert data["output"] == "1. Define backend\n2. Define frontend"
    assert data["status"] == "completed"
    assert data["error"] is None
    assert data["started_at"] is not None
    assert data["completed_at"] is not None
    assert data["duration_ms"] >= 0
    assert mock_client.calls[0][1] == "Create an AI agent orchestration dashboard"


def test_run_planner_endpoint_validates_empty_task() -> None:
    mock_client = MockOpenRouterClient()
    app.dependency_overrides[get_openrouter_client] = lambda: mock_client

    try:
        client = TestClient(app)
        response = client.post("/api/agents/planner/run", json={"task": ""})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_client.calls == []
