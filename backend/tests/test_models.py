from datetime import UTC, datetime

import pytest
from app.models.agent import (
    AgentDefinition,
    AgentExecutionInput,
    AgentExecutionResult,
    AgentRole,
)
from app.models.workflow import WorkflowResult, WorkflowRun, WorkflowStatus, WorkflowStep
from app.models.workflow_event import WorkflowEvent, WorkflowEventType
from pydantic import ValidationError


def test_agent_definition_creation() -> None:
    agent = AgentDefinition(
        role=AgentRole.PLANNER,
        name="  Planner Agent  ",
        description="  Breaks a task into execution steps.  ",
        system_prompt="  You are a planning agent.  ",
    )

    assert agent.id
    assert agent.role == AgentRole.PLANNER
    assert agent.name == "Planner Agent"
    assert agent.description == "Breaks a task into execution steps."
    assert agent.system_prompt == "You are a planning agent."


@pytest.mark.parametrize(
    "field_values",
    [
        {"name": ""},
        {"name": "   "},
        {"description": ""},
        {"system_prompt": ""},
    ],
)
def test_agent_definition_rejects_blank_text_fields(field_values: dict[str, str]) -> None:
    payload = {
        "role": AgentRole.PLANNER,
        "name": "Planner Agent",
        "description": "Breaks a task into execution steps.",
        "system_prompt": "You are a planning agent.",
        **field_values,
    }

    with pytest.raises(ValidationError):
        AgentDefinition(**payload)


@pytest.mark.parametrize(
    ("model_class", "payload"),
    [
        (
            AgentDefinition,
            {
                "role": AgentRole.PLANNER,
                "name": "Planner Agent",
                "description": "Breaks a task into execution steps.",
                "system_prompt": "You are a planning agent.",
            },
        ),
        (AgentExecutionInput, {"role": AgentRole.PLANNER, "input": "Create a plan"}),
        (AgentExecutionResult, {"role": AgentRole.PLANNER}),
    ],
)
@pytest.mark.parametrize("model_id", ["", ".agent-1", "agent/1", "x" * 65])
def test_agent_models_reject_invalid_ids(
    model_class: type[AgentDefinition | AgentExecutionInput | AgentExecutionResult],
    payload: dict[str, object],
    model_id: str,
) -> None:
    with pytest.raises(ValidationError):
        model_class(id=model_id, **payload)


def test_agent_execution_input_creation() -> None:
    execution_input = AgentExecutionInput(
        role="researcher",
        input="  What should the workflow research?  ",
    )

    assert execution_input.role == AgentRole.RESEARCHER
    assert execution_input.input == "What should the workflow research?"


def test_agent_execution_input_accepts_structured_input() -> None:
    execution_input = AgentExecutionInput(
        role="researcher",
        input={"question": "What should the workflow research?"},
    )

    assert execution_input.input == {"question": "What should the workflow research?"}


@pytest.mark.parametrize("agent_input", ["", "   ", {}])
def test_agent_execution_input_rejects_empty_input(agent_input: str | dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        AgentExecutionInput(role="researcher", input=agent_input)


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
        name="  Design backend structure  ",
        description="  Create the folder and module layout.  ",
        input="  Original task  ",
        output="  Architecture plan  ",
        status="running",
    )

    assert step.id
    assert step.role == AgentRole.TECHNICAL_ARCHITECT
    assert step.name == "Design backend structure"
    assert step.description == "Create the folder and module layout."
    assert step.input == "Original task"
    assert step.output == "Architecture plan"
    assert step.status == WorkflowStatus.RUNNING


@pytest.mark.parametrize(
    "field_values",
    [
        {"name": ""},
        {"name": "   "},
        {"description": ""},
    ],
)
def test_workflow_step_rejects_blank_text_fields(field_values: dict[str, str]) -> None:
    payload = {
        "role": AgentRole.TECHNICAL_ARCHITECT,
        "name": "Design backend structure",
        **field_values,
    }

    with pytest.raises(ValidationError):
        WorkflowStep(**payload)


@pytest.mark.parametrize(
    "field_values",
    [
        {"input": ""},
        {"input": {}},
        {"output": ""},
        {"output": {}},
        {"error": ""},
    ],
)
def test_workflow_step_rejects_empty_payload_fields(field_values: dict[str, object]) -> None:
    payload = {
        "role": AgentRole.TECHNICAL_ARCHITECT,
        "name": "Design backend structure",
        **field_values,
    }

    with pytest.raises(ValidationError):
        WorkflowStep(**payload)


@pytest.mark.parametrize(
    ("model_class", "payload"),
    [
        (WorkflowStep, {"role": AgentRole.PLANNER, "name": "Planner Agent"}),
        (WorkflowRun, {"input": "Create a plan"}),
        (WorkflowResult, {"status": WorkflowStatus.COMPLETED}),
    ],
)
@pytest.mark.parametrize("model_id", ["", ".workflow-1", "workflow/1", "x" * 65])
def test_workflow_models_reject_invalid_ids(
    model_class: type[WorkflowStep | WorkflowRun | WorkflowResult],
    payload: dict[str, object],
    model_id: str,
) -> None:
    with pytest.raises(ValidationError):
        model_class(id=model_id, **payload)


def test_workflow_run_creation_defaults_to_pending() -> None:
    run = WorkflowRun(input="  Build an orchestration dashboard  ")

    assert run.id
    assert run.input == "Build an orchestration dashboard"
    assert run.status == WorkflowStatus.PENDING
    assert run.steps == []


@pytest.mark.parametrize("workflow_input", ["", "   ", {}])
def test_workflow_run_rejects_empty_input(workflow_input: str | dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        WorkflowRun(input=workflow_input)


def test_workflow_result_creation() -> None:
    step = WorkflowStep(
        role=AgentRole.FINAL_ANSWER,
        name="Prepare final answer",
        output="Final response ready.",
        status=WorkflowStatus.COMPLETED,
    )

    result = WorkflowResult(
        input="  Create project foundation  ",
        output="  Project foundation created.  ",
        final_answer="  Project foundation created.  ",
        status=WorkflowStatus.COMPLETED,
        steps=[step],
        duration_ms=500,
    )

    assert result.status == WorkflowStatus.COMPLETED
    assert result.input == "Create project foundation"
    assert result.output == "Project foundation created."
    assert result.final_answer == "Project foundation created."
    assert result.steps[0].role == AgentRole.FINAL_ANSWER
    assert result.duration_ms == 500


@pytest.mark.parametrize(
    "field_values",
    [
        {"input": ""},
        {"input": {}},
        {"output": ""},
        {"output": {}},
        {"final_answer": ""},
        {"error": ""},
    ],
)
def test_workflow_result_rejects_empty_provided_values(field_values: dict[str, object]) -> None:
    payload = {"status": WorkflowStatus.COMPLETED, **field_values}

    with pytest.raises(ValidationError):
        WorkflowResult(**payload)


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


@pytest.mark.parametrize("workflow_id", ["", ".workflow-1", "workflow/1", "x" * 65])
def test_workflow_event_rejects_invalid_workflow_ids(workflow_id: str) -> None:
    with pytest.raises(ValidationError):
        WorkflowEvent(workflow_id=workflow_id, event=WorkflowEventType.WORKFLOW_STARTED)


@pytest.mark.parametrize("event_id", ["", ".event-1", "event/1", "x" * 65])
def test_workflow_event_rejects_invalid_event_ids(event_id: str) -> None:
    with pytest.raises(ValidationError):
        WorkflowEvent(
            id=event_id,
            workflow_id="workflow-1",
            event=WorkflowEventType.WORKFLOW_STARTED,
        )


def test_workflow_event_strips_message_text() -> None:
    event = WorkflowEvent(
        workflow_id="workflow-1",
        event=WorkflowEventType.WORKFLOW_STARTED,
        message="  Workflow started.  ",
    )

    assert event.message == "Workflow started."


@pytest.mark.parametrize("message", ["", "   "])
def test_workflow_event_rejects_blank_message_text(message: str) -> None:
    with pytest.raises(ValidationError):
        WorkflowEvent(
            workflow_id="workflow-1",
            event=WorkflowEventType.WORKFLOW_STARTED,
            message=message,
        )
