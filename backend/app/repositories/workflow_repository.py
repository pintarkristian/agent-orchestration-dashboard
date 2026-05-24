from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import AgentExecutionStepRecord, WorkflowRunRecord
from app.models.enums import AgentRole, WorkflowStatus
from app.models.workflow import WorkflowResult, WorkflowStep

_SERIALIZED_VALUE_KIND = "kind"
_SERIALIZED_VALUE_MARKER = "__ai_agent_orchestration_dashboard_value__"
_SERIALIZED_VALUE_STRUCTURED = "structured"
_SERIALIZED_VALUE_TEXT = "text"


class WorkflowRepository:
    """Repository for persisted workflow runs and agent steps."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save_workflow_result(self, result: WorkflowResult) -> WorkflowResult:
        """Persist a completed or failed workflow result."""
        created_at = result.created_at or result.started_at or datetime.now(UTC)
        duration_ms = (
            result.total_duration_ms if result.total_duration_ms is not None else result.duration_ms
        )

        record = WorkflowRunRecord(
            id=result.id,
            original_task=self._serialize_value(result.input) or "",
            status=result.status.value,
            final_answer=self._serialize(result.final_answer),
            error=result.error,
            created_at=created_at,
            completed_at=result.completed_at,
            duration_ms=duration_ms,
        )

        record.steps = [
            AgentExecutionStepRecord(
                id=step.id,
                workflow_id=result.id,
                position=index,
                agent_role=step.role.value,
                name=step.name,
                description=step.description,
                input=self._serialize_value(step.input),
                output=self._serialize_value(step.output),
                status=step.status.value,
                error=step.error,
                started_at=step.started_at,
                completed_at=step.completed_at,
                duration_ms=step.duration_ms,
            )
            for index, step in enumerate(result.steps)
        ]

        self.db.merge(record)
        self.db.commit()

        saved = self.get_workflow(result.id)
        if saved is None:
            raise RuntimeError(f"Workflow {result.id} was not persisted correctly")
        return saved

    def list_workflows(self) -> list[WorkflowResult]:
        """Return all workflow runs, newest first."""
        statement = (
            select(WorkflowRunRecord)
            .options(selectinload(WorkflowRunRecord.steps))
            .order_by(WorkflowRunRecord.created_at.desc())
        )
        records = self.db.scalars(statement).all()
        return [self._to_workflow_result(record) for record in records]

    def get_workflow(self, workflow_id: str) -> WorkflowResult | None:
        """Return one workflow run by id."""
        statement = (
            select(WorkflowRunRecord)
            .where(WorkflowRunRecord.id == workflow_id)
            .options(selectinload(WorkflowRunRecord.steps))
        )
        record = self.db.scalars(statement).first()
        if record is None:
            return None
        return self._to_workflow_result(record)

    def _to_workflow_result(self, record: WorkflowRunRecord) -> WorkflowResult:
        steps = [
            WorkflowStep(
                id=step.id,
                role=AgentRole(step.agent_role),
                name=step.name,
                description=step.description,
                input=self._deserialize_value(step.input),
                output=self._deserialize_value(step.output),
                status=WorkflowStatus(step.status),
                error=step.error,
                started_at=step.started_at,
                completed_at=step.completed_at,
                duration_ms=step.duration_ms,
            )
            for step in sorted(record.steps, key=lambda item: item.position)
        ]

        return WorkflowResult(
            id=record.id,
            input=self._deserialize_value(record.original_task),
            output=record.final_answer,
            final_answer=record.final_answer,
            status=WorkflowStatus(record.status),
            steps=steps,
            error=record.error,
            created_at=record.created_at,
            started_at=record.created_at,
            completed_at=record.completed_at,
            duration_ms=record.duration_ms,
            total_duration_ms=record.duration_ms,
        )

    @staticmethod
    def _serialize(value: Any) -> str | None:
        """Store string values directly and JSON-encode fallback values."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _serialize_value(value: str | dict[str, Any] | None) -> str | None:
        """Store workflow values with a marker that preserves their original type."""
        if value is None:
            return None

        value_kind = (
            _SERIALIZED_VALUE_TEXT if isinstance(value, str) else _SERIALIZED_VALUE_STRUCTURED
        )
        return json.dumps(
            {
                _SERIALIZED_VALUE_MARKER: True,
                _SERIALIZED_VALUE_KIND: value_kind,
                "value": value,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _deserialize_value(value: str | None) -> str | dict[str, Any] | None:
        """Restore structured workflow values without changing ordinary strings."""
        if value is None:
            return None

        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value

        if not isinstance(decoded, dict) or decoded.get(_SERIALIZED_VALUE_MARKER) is not True:
            return value

        decoded_value = decoded.get("value")
        if decoded.get(_SERIALIZED_VALUE_KIND) == _SERIALIZED_VALUE_TEXT and isinstance(
            decoded_value,
            str,
        ):
            return decoded_value

        if decoded.get(_SERIALIZED_VALUE_KIND) == _SERIALIZED_VALUE_STRUCTURED and isinstance(
            decoded_value,
            dict,
        ):
            return decoded_value

        if _SERIALIZED_VALUE_KIND not in decoded and isinstance(decoded_value, dict):
            return decoded_value

        return value


__all__ = ["WorkflowRepository"]
