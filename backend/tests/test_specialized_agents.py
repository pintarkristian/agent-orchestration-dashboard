import pytest
from app.agents import (
    DeveloperAgent,
    FinalAnswerAgent,
    PlannerAgent,
    ResearchAgent,
    ReviewerAgent,
    TechnicalArchitectAgent,
)
from app.agents.base_agent import BaseAgent
from app.models.enums import AgentRole, WorkflowStatus


class MockOpenRouterClient:
    def __init__(self, response: str = "Mocked agent output") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("agent_class", "expected_role", "expected_prompt_text"),
    [
        (PlannerAgent, AgentRole.PLANNER, "break"),
        (ResearchAgent, AgentRole.RESEARCHER, "background context"),
        (TechnicalArchitectAgent, AgentRole.TECHNICAL_ARCHITECT, "architecture"),
        (DeveloperAgent, AgentRole.DEVELOPER, "implementation"),
        (ReviewerAgent, AgentRole.REVIEWER, "quality"),
        (FinalAnswerAgent, AgentRole.FINAL_ANSWER, "final response"),
    ],
)
async def test_each_agent_can_run_with_mocked_openrouter_client(
    agent_class: type[BaseAgent],
    expected_role: AgentRole,
    expected_prompt_text: str,
) -> None:
    mock_client = MockOpenRouterClient(response=f"Output from {expected_role.value}")
    agent = agent_class(openrouter_client=mock_client)

    result = await agent.run("Build an AI agent orchestration dashboard")

    assert result.role == expected_role
    assert result.input == "Build an AI agent orchestration dashboard"
    assert result.output == f"Output from {expected_role.value}"
    assert result.status == WorkflowStatus.COMPLETED
    assert result.error is None
    assert result.started_at is not None
    assert result.completed_at is not None
    assert result.duration_ms is not None
    assert result.duration_ms >= 0

    assert agent.role == expected_role
    assert agent.name
    assert agent.description
    assert expected_prompt_text in agent.system_prompt.lower()
    assert mock_client.calls == [(agent.system_prompt, "Build an AI agent orchestration dashboard")]
