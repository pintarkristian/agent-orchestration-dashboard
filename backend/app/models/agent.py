from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import AgentRole, WorkflowStatus


class AgentDefinition(BaseModel):
    """Static configuration for one orchestration agent."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: AgentRole
    name: str
    description: str
    system_prompt: str


class AgentExecutionInput(BaseModel):
    """Input payload passed to an agent during a workflow run."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: AgentRole
    input: str | dict[str, Any]


class AgentExecutionResult(BaseModel):
    """Result produced by an agent after execution."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: AgentRole
    input: str | dict[str, Any] | None = None
    output: str | dict[str, Any] | None = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)


__all__ = [
    "AgentDefinition",
    "AgentExecutionInput",
    "AgentExecutionResult",
    "AgentRole",
]
