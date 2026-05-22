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

    received = []
    async for event in bus.subscribe("workflow-2"):
        received.append(event.event)

    assert received == [
        WorkflowEventType.WORKFLOW_STARTED,
        WorkflowEventType.WORKFLOW_COMPLETED,
    ]
