from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AgentRole, WorkflowStatus
from app.models.identifiers import WORKFLOW_ID_MAX_LENGTH, WORKFLOW_ID_PATTERN
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

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        min_length=1,
        max_length=WORKFLOW_ID_MAX_LENGTH,
        pattern=WORKFLOW_ID_PATTERN,
    )
    workflow_id: str = Field(
        min_length=1,
        max_length=WORKFLOW_ID_MAX_LENGTH,
        pattern=WORKFLOW_ID_PATTERN,
    )
    event: WorkflowEventType
    status: WorkflowStatus | None = None
    role: AgentRole | None = None
    step: WorkflowStep | None = None
    workflow: WorkflowResult | None = None
    message: str | None = Field(default=None, min_length=1)
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
