from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AgentRole, WorkflowStatus


class AgentDefinition(BaseModel):
    """Static configuration for one orchestration agent."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: AgentRole
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)


class AgentExecutionInput(BaseModel):
    """Input payload passed to an agent during a workflow run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: AgentRole
    input: str | dict[str, Any] = Field(min_length=1)


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
