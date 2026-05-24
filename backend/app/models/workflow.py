from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AgentRole, WorkflowStatus


class WorkflowStep(BaseModel):
    """One agent step inside an orchestration workflow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: AgentRole
    name: str = Field(min_length=1)
    description: str | None = Field(default=None, min_length=1)
    input: str | dict[str, Any] | None = None
    output: str | dict[str, Any] | None = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    error: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)


class WorkflowRun(BaseModel):
    """Runtime representation of a full multi-agent workflow execution."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    input: str | dict[str, Any] = Field(min_length=1)
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: list[WorkflowStep] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)


class WorkflowResult(BaseModel):
    """Final result returned after a workflow finishes."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    input: str | dict[str, Any] | None = None
    output: str | dict[str, Any] | None = None
    final_answer: str | None = None
    status: WorkflowStatus
    steps: list[WorkflowStep] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    total_duration_ms: int | None = Field(default=None, ge=0)


__all__ = [
    "WorkflowResult",
    "WorkflowRun",
    "WorkflowStatus",
    "WorkflowStep",
]
