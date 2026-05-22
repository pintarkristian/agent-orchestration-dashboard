from datetime import UTC, datetime

import pytest
from app.models.agent import (
    AgentDefinition,
    AgentExecutionInput,
    AgentExecutionResult,
    AgentRole,
)
from app.models.workflow import WorkflowResult, WorkflowRun, WorkflowStatus, WorkflowStep
from pydantic import ValidationError


def test_agent_definition_creation() -> None:
    agent = AgentDefinition(
        role=AgentRole.PLANNER,
        name="Planner Agent",
        description="Breaks a task into execution steps.",
        system_prompt="You are a planning agent.",
    )

    assert agent.id
    assert agent.role == AgentRole.PLANNER
    assert agent.name == "Planner Agent"
    assert agent.system_prompt == "You are a planning agent."


def test_agent_execution_input_creation() -> None:
    execution_input = AgentExecutionInput(
        role="researcher",
        input={"question": "What should the workflow research?"},
    )

    assert execution_input.role == AgentRole.RESEARCHER
    assert execution_input.input == {"question": "What should the workflow research?"}


def test_agent_execution_result_creation_with_status_and_timing() -> None:
    started_at = datetime.now(UTC)
    completed_at = datetime.now(UTC)

    result = AgentExecutionResult(
        role=AgentRole.DEVELOPER,
        input="Create the API skeleton.",
        output="API skeleton created.",
        status=WorkflowStatus.COMPLETED,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=125,
    )

    assert result.status == WorkflowStatus.COMPLETED
    assert result.error is None
    assert result.duration_ms == 125


def test_workflow_step_creation() -> None:
    step = WorkflowStep(
        role=AgentRole.TECHNICAL_ARCHITECT,
        name="Design backend structure",
        description="Create the folder and module layout.",
        status="running",
    )

    assert step.id
    assert step.role == AgentRole.TECHNICAL_ARCHITECT
    assert step.status == WorkflowStatus.RUNNING


def test_workflow_run_creation_defaults_to_pending() -> None:
    run = WorkflowRun(input="Build an orchestration dashboard")

    assert run.id
    assert run.status == WorkflowStatus.PENDING
    assert run.steps == []


def test_workflow_result_creation() -> None:
    step = WorkflowStep(
        role=AgentRole.FINAL_ANSWER,
        name="Prepare final answer",
        output="Final response ready.",
        status=WorkflowStatus.COMPLETED,
    )

    result = WorkflowResult(
        input="Create project foundation",
        output="Project foundation created.",
        status=WorkflowStatus.COMPLETED,
        steps=[step],
        duration_ms=500,
    )

    assert result.status == WorkflowStatus.COMPLETED
    assert result.steps[0].role == AgentRole.FINAL_ANSWER
    assert result.duration_ms == 500


def test_agent_role_values() -> None:
    assert {role.value for role in AgentRole} == {
        "planner",
        "researcher",
        "technical_architect",
        "developer",
        "reviewer",
        "final_answer",
    }


def test_workflow_status_values() -> None:
    assert {status.value for status in WorkflowStatus} == {
        "pending",
        "running",
        "completed",
        "failed",
    }


def test_negative_duration_is_rejected() -> None:
    with pytest.raises(ValidationError):
        WorkflowRun(input="Invalid duration", duration_ms=-1)
