from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.models.identifiers import WORKFLOW_ID_MAX_LENGTH


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


class WorkflowRunRecord(Base):
    """Persisted workflow run."""

    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(WORKFLOW_ID_MAX_LENGTH), primary_key=True, index=True)
    original_task: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    final_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    steps: Mapped[list[AgentExecutionStepRecord]] = relationship(
        "AgentExecutionStepRecord",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="AgentExecutionStepRecord.position",
    )


class AgentExecutionStepRecord(Base):
    """Persisted agent execution step for a workflow."""

    __tablename__ = "agent_execution_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    workflow_id: Mapped[str] = mapped_column(
        String(WORKFLOW_ID_MAX_LENGTH),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    input: Mapped[str | None] = mapped_column(Text, nullable=True)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    workflow: Mapped[WorkflowRunRecord] = relationship(
        "WorkflowRunRecord",
        back_populates="steps",
    )


__all__ = ["AgentExecutionStepRecord", "Base", "WorkflowRunRecord"]
