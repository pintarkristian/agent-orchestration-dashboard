from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import AgentRole, WorkflowStatus
from app.models.workflow import WorkflowResult, WorkflowStep


class WorkflowEventType(str, Enum):
    """Server-Sent Event names emitted while a workflow runs."""

    WORKFLOW_STARTED = "workflow_started"
    AGENT_PENDING = "agent_pending"
    AGENT_RUNNING = "agent_running"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"


class WorkflowEvent(BaseModel):
    """A typed event sent to frontend clients over Server-Sent Events."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    event: WorkflowEventType
    status: WorkflowStatus | None = None
    role: AgentRole | None = None
    step: WorkflowStep | None = None
    workflow: WorkflowResult | None = None
    message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


TERMINAL_WORKFLOW_EVENTS = {
    WorkflowEventType.WORKFLOW_COMPLETED,
    WorkflowEventType.WORKFLOW_FAILED,
}


__all__ = [
    "TERMINAL_WORKFLOW_EVENTS",
    "WorkflowEvent",
    "WorkflowEventType",
]
