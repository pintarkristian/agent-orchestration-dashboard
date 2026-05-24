"""Shared identifier constraints used across API, models, and persistence."""

import re

WORKFLOW_ID_MAX_LENGTH = 64
WORKFLOW_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
_WORKFLOW_ID_REGEX = re.compile(WORKFLOW_ID_PATTERN)


def validate_workflow_id(value: str) -> str:
    """Normalize and validate a workflow id outside Pydantic/FastAPI boundaries."""
    workflow_id = value.strip()
    if not workflow_id:
        raise ValueError("workflow_id must not be blank")
    invalid_length = len(workflow_id) > WORKFLOW_ID_MAX_LENGTH
    invalid_pattern = _WORKFLOW_ID_REGEX.fullmatch(workflow_id) is None
    if invalid_length or invalid_pattern:
        raise ValueError("workflow_id has an invalid format")
    return workflow_id


__all__ = ["WORKFLOW_ID_MAX_LENGTH", "WORKFLOW_ID_PATTERN", "validate_workflow_id"]
