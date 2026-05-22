from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.api.routes.workflows import get_orchestrator
from app.main import app
from app.models.agent import AgentExecutionResult
from app.models.enums import AgentRole, WorkflowStatus
from app.services.orchestrator import SequentialOrchestrator
from fastapi.testclient import TestClient


class MockAgent:
    def __init__(self, role: AgentRole, output: str, should_fail: bool = False) -> None:
        self.role = role
        self.name = f"{role.value.title()} Agent"
        self.description = f"Mock {role.value} agent."
        self.output = output
        self.should_fail = should_fail
        self.inputs: list[str] = []

    async def run(self, input_text: str) -> AgentExecutionResult:
        self.inputs.append(input_text)
        started_at = datetime.now(UTC)
        completed_at = datetime.now(UTC)

        if self.should_fail:
            return AgentExecutionResult(
                role=self.role,
                input=input_text,
                output=None,
                status=WorkflowStatus.FAILED,
                error=f"{self.role.value} failed",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=0,
            )

        return AgentExecutionResult(
            role=self.role,
            input=input_text,
            output=self.output,
            status=WorkflowStatus.COMPLETED,
            error=None,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=0,
        )


class MockOrchestrator:
    async def run(self, task: str, workflow_id: str | None = None):
        return await SequentialOrchestrator(
            agents=[
                MockAgent(AgentRole.PLANNER, "Planner output"),
                MockAgent(AgentRole.RESEARCHER, "Research output"),
                MockAgent(AgentRole.TECHNICAL_ARCHITECT, "Architecture output"),
                MockAgent(AgentRole.DEVELOPER, "Developer output"),
                MockAgent(AgentRole.REVIEWER, "Reviewer output"),
                MockAgent(AgentRole.FINAL_ANSWER, "Final answer output"),
            ]
        ).run(task, workflow_id=workflow_id)


def build_mock_agents(failing_role: AgentRole | None = None) -> list[MockAgent]:
    return [
        MockAgent(AgentRole.PLANNER, "Planner output", failing_role == AgentRole.PLANNER),
        MockAgent(AgentRole.RESEARCHER, "Research output", failing_role == AgentRole.RESEARCHER),
        MockAgent(
            AgentRole.TECHNICAL_ARCHITECT,
            "Architecture output",
            failing_role == AgentRole.TECHNICAL_ARCHITECT,
        ),
        MockAgent(AgentRole.DEVELOPER, "Developer output", failing_role == AgentRole.DEVELOPER),
        MockAgent(AgentRole.REVIEWER, "Reviewer output", failing_role == AgentRole.REVIEWER),
        MockAgent(
            AgentRole.FINAL_ANSWER,
            "Final answer output",
            failing_role == AgentRole.FINAL_ANSWER,
        ),
    ]


@pytest.mark.asyncio
async def test_sequential_orchestrator_runs_agents_in_order() -> None:
    agents = build_mock_agents()
    orchestrator = SequentialOrchestrator(agents=agents)

    result = await orchestrator.run("Build an AI orchestration dashboard")

    assert result.id
    assert result.status == WorkflowStatus.COMPLETED
    assert result.final_answer == "Final answer output"
    assert result.output == "Final answer output"
    assert result.error is None
    assert result.duration_ms is not None
    assert result.total_duration_ms is not None
    assert [step.role for step in result.steps] == [
        AgentRole.PLANNER,
        AgentRole.RESEARCHER,
        AgentRole.TECHNICAL_ARCHITECT,
        AgentRole.DEVELOPER,
        AgentRole.REVIEWER,
        AgentRole.FINAL_ANSWER,
    ]
    assert all(step.status == WorkflowStatus.COMPLETED for step in result.steps)


@pytest.mark.asyncio
async def test_sequential_orchestrator_passes_previous_outputs_to_next_agents() -> None:
    agents = build_mock_agents()
    orchestrator = SequentialOrchestrator(agents=agents)

    await orchestrator.run("Create a product plan")

    assert "Original user task" in agents[0].inputs[0]
    assert "Create a product plan" in agents[0].inputs[0]
    assert "Planner output" in agents[1].inputs[0]
    assert "Research output" in agents[2].inputs[0]
    assert "Architecture output" in agents[3].inputs[0]
    assert "Developer output" in agents[4].inputs[0]
    assert "Reviewer output" in agents[5].inputs[0]


@pytest.mark.asyncio
async def test_sequential_orchestrator_stops_when_agent_fails() -> None:
    agents = build_mock_agents(failing_role=AgentRole.DEVELOPER)
    orchestrator = SequentialOrchestrator(agents=agents)

    result = await orchestrator.run("Create a technical plan")

    assert result.status == WorkflowStatus.FAILED
    assert result.final_answer is None
    assert result.output is None
    assert result.error == "Workflow stopped because Developer Agent failed: developer failed"
    assert [step.role for step in result.steps] == [
        AgentRole.PLANNER,
        AgentRole.RESEARCHER,
        AgentRole.TECHNICAL_ARCHITECT,
        AgentRole.DEVELOPER,
    ]
    assert result.steps[-1].status == WorkflowStatus.FAILED
    assert agents[4].inputs == []
    assert agents[5].inputs == []


def test_run_workflow_endpoint_returns_workflow_result() -> None:
    app.dependency_overrides[get_orchestrator] = lambda: MockOrchestrator()

    try:
        client = TestClient(app)
        response = client.post(
            "/api/workflows/run",
            json={"task": "Analyze this startup idea and create a technical implementation plan."},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()
    assert data["id"]
    assert data["status"] == "completed"
    assert data["final_answer"] == "Final answer output"
    assert data["output"] == "Final answer output"
    assert data["error"] is None
    assert data["duration_ms"] >= 0
    assert data["total_duration_ms"] >= 0
    assert [step["role"] for step in data["steps"]] == [
        "planner",
        "researcher",
        "technical_architect",
        "developer",
        "reviewer",
        "final_answer",
    ]


def test_run_workflow_endpoint_validates_empty_task() -> None:
    app.dependency_overrides[get_orchestrator] = lambda: MockOrchestrator()

    try:
        client = TestClient(app)
        response = client.post("/api/workflows/run", json={"task": ""})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
