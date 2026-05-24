from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.identifiers import WORKFLOW_ID_MAX_LENGTH, WORKFLOW_ID_PATTERN
from app.models.workflow import WorkflowResult
from app.models.workflow_event import TERMINAL_WORKFLOW_EVENTS
from app.repositories.workflow_repository import WorkflowRepository
from app.services.openrouter_client import OpenRouterClient
from app.services.orchestrator import SequentialOrchestrator
from app.services.workflow_events import format_sse, workflow_event_bus

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
WorkflowIdPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=WORKFLOW_ID_MAX_LENGTH,
        pattern=WORKFLOW_ID_PATTERN,
        description="Workflow id.",
    ),
]


class WorkflowRunRequest(BaseModel):
    """Request payload for running a sequential workflow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task: str = Field(
        ...,
        min_length=1,
        description="User task to process through the full agent workflow.",
    )
    workflow_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=WORKFLOW_ID_MAX_LENGTH,
        pattern=WORKFLOW_ID_PATTERN,
        description="Optional client-generated workflow id used for live event subscriptions.",
    )


def get_openrouter_client() -> OpenRouterClient:
    """Create the OpenRouter client dependency."""
    return OpenRouterClient()


def get_workflow_repository(db: Annotated[Session, Depends(get_db)]) -> WorkflowRepository:
    """Create the workflow repository dependency."""
    return WorkflowRepository(db)


def get_orchestrator(
    openrouter_client: Annotated[OpenRouterClient, Depends(get_openrouter_client)],
    workflow_repository: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
) -> SequentialOrchestrator:
    """Create the sequential orchestrator dependency."""
    return SequentialOrchestrator(
        openrouter_client=openrouter_client,
        workflow_repository=workflow_repository,
        event_publisher=workflow_event_bus,
    )


@router.get("", response_model=list[WorkflowResult])
def list_workflows(
    workflow_repository: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
) -> list[WorkflowResult]:
    """Return persisted workflow runs."""
    return workflow_repository.list_workflows()


@router.post("/run", response_model=WorkflowResult)
async def run_workflow(
    request: WorkflowRunRequest,
    orchestrator: Annotated[SequentialOrchestrator, Depends(get_orchestrator)],
    workflow_repository: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
) -> WorkflowResult:
    """Run a task through the complete sequential agent workflow and persist it."""
    if request.workflow_id and workflow_repository.get_workflow(request.workflow_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow '{request.workflow_id}' already exists.",
        )

    return await orchestrator.run(request.task, workflow_id=request.workflow_id)


@router.get("/{workflow_id}/events")
async def stream_workflow_events(
    workflow_id: WorkflowIdPath,
    request: Request,
) -> StreamingResponse:
    """Stream real-time workflow updates as Server-Sent Events."""

    async def event_stream() -> AsyncIterator[str]:
        async for event in workflow_event_bus.subscribe(workflow_id):
            if await request.is_disconnected():
                break
            yield format_sse(event)
            if event.event in TERMINAL_WORKFLOW_EVENTS:
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{workflow_id}", response_model=WorkflowResult)
def get_workflow(
    workflow_id: WorkflowIdPath,
    workflow_repository: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
) -> WorkflowResult:
    """Return a persisted workflow run by id."""
    workflow = workflow_repository.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' was not found.",
        )
    return workflow
