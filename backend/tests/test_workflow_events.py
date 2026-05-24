from __future__ import annotations

import json

import pytest
from app.models.enums import AgentRole, WorkflowStatus
from app.models.workflow import WorkflowStep
from app.models.workflow_event import WorkflowEvent, WorkflowEventType
from app.services.workflow_events import WorkflowEventBus, format_sse


def test_format_sse_includes_named_event_id_and_json_data() -> None:
    event = WorkflowEvent(
        id="event-1",
        workflow_id="workflow-1",
        event=WorkflowEventType.AGENT_RUNNING,
        status=WorkflowStatus.RUNNING,
        role=AgentRole.PLANNER,
        step=WorkflowStep(
            id="step-1",
            role=AgentRole.PLANNER,
            name="Planner Agent",
            description="Breaks a task into steps.",
            input="Original user task",
            output=None,
            status=WorkflowStatus.RUNNING,
        ),
        message="Planner Agent is running.",
    )

    frame = format_sse(event)

    assert frame.startswith("event: agent_running\n")
    assert "id: event-1\n" in frame
    assert frame.endswith("\n\n")

    data_line = next(line for line in frame.splitlines() if line.startswith("data: "))
    payload = json.loads(data_line.removeprefix("data: "))

    assert payload["workflow_id"] == "workflow-1"
    assert payload["event"] == "agent_running"
    assert payload["status"] == "running"
    assert payload["role"] == "planner"
    assert payload["step"]["status"] == "running"


@pytest.mark.asyncio
async def test_workflow_event_bus_replays_history_and_stops_after_terminal_event() -> None:
    bus = WorkflowEventBus()
    await bus.publish(
        WorkflowEvent(
            workflow_id="workflow-2",
            event=WorkflowEventType.WORKFLOW_STARTED,
            status=WorkflowStatus.RUNNING,
            message="Workflow started.",
        )
    )
    await bus.publish(
        WorkflowEvent(
            workflow_id="workflow-2",
            event=WorkflowEventType.WORKFLOW_COMPLETED,
            status=WorkflowStatus.COMPLETED,
            message="Workflow completed.",
        )
    )

    received = [event.event async for event in bus.subscribe("workflow-2")]

    assert received == [
        WorkflowEventType.WORKFLOW_STARTED,
        WorkflowEventType.WORKFLOW_COMPLETED,
    ]


@pytest.mark.asyncio
async def test_workflow_event_bus_limits_replay_history() -> None:
    bus = WorkflowEventBus(max_history_per_workflow=2)
    await bus.publish(
        WorkflowEvent(
            workflow_id="workflow-3",
            event=WorkflowEventType.WORKFLOW_STARTED,
            status=WorkflowStatus.RUNNING,
            message="Workflow started.",
        )
    )
    await bus.publish(
        WorkflowEvent(
            workflow_id="workflow-3",
            event=WorkflowEventType.AGENT_RUNNING,
            status=WorkflowStatus.RUNNING,
            role=AgentRole.PLANNER,
            message="Planner running.",
        )
    )
    await bus.publish(
        WorkflowEvent(
            workflow_id="workflow-3",
            event=WorkflowEventType.WORKFLOW_COMPLETED,
            status=WorkflowStatus.COMPLETED,
            message="Workflow completed.",
        )
    )

    received = [event.event async for event in bus.subscribe("workflow-3")]

    assert received == [
        WorkflowEventType.AGENT_RUNNING,
        WorkflowEventType.WORKFLOW_COMPLETED,
    ]


@pytest.mark.asyncio
async def test_workflow_event_bus_ignores_events_after_terminal_event() -> None:
    bus = WorkflowEventBus()
    await bus.publish(
        WorkflowEvent(
            workflow_id="workflow-4",
            event=WorkflowEventType.WORKFLOW_STARTED,
            status=WorkflowStatus.RUNNING,
        )
    )
    await bus.publish(
        WorkflowEvent(
            workflow_id="workflow-4",
            event=WorkflowEventType.WORKFLOW_COMPLETED,
            status=WorkflowStatus.COMPLETED,
        )
    )
    await bus.publish(
        WorkflowEvent(
            workflow_id="workflow-4",
            event=WorkflowEventType.AGENT_RUNNING,
            status=WorkflowStatus.RUNNING,
            role=AgentRole.PLANNER,
        )
    )

    received = [event.event async for event in bus.subscribe("workflow-4")]

    assert received == [
        WorkflowEventType.WORKFLOW_STARTED,
        WorkflowEventType.WORKFLOW_COMPLETED,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("workflow_id", ["", "   ", ".workflow-1", "workflow/1", "x" * 65])
async def test_workflow_event_bus_rejects_invalid_subscription_ids(workflow_id: str) -> None:
    bus = WorkflowEventBus()

    with pytest.raises(ValueError):
        async for _event in bus.subscribe(workflow_id):
            pass


def test_workflow_event_bus_rejects_invalid_history_limit() -> None:
    with pytest.raises(ValueError, match="max_history_per_workflow must be at least 1"):
        WorkflowEventBus(max_history_per_workflow=0)
