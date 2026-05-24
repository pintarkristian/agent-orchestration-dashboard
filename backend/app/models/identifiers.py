"""Shared identifier constraints used across API, models, and persistence."""

WORKFLOW_ID_MAX_LENGTH = 64
WORKFLOW_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"

__all__ = ["WORKFLOW_ID_MAX_LENGTH", "WORKFLOW_ID_PATTERN"]
