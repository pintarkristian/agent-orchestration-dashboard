from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator

from app.models.workflow_event import TERMINAL_WORKFLOW_EVENTS, WorkflowEvent


class WorkflowEventBus:
    """Small in-memory pub/sub bus for live workflow events.

    The backend still returns the final workflow from ``POST /api/workflows/run``.
    This bus gives the React frontend live status updates while that request is
    running. It intentionally keeps recent events in memory so clients can
    connect shortly after a workflow starts and still receive already emitted
    events.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[WorkflowEvent]]] = defaultdict(set)
        self._history: dict[str, list[WorkflowEvent]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event: WorkflowEvent) -> None:
        """Publish one workflow event to active subscribers and history."""
        async with self._lock:
            self._history[event.workflow_id].append(event)
            subscribers = list(self._subscribers.get(event.workflow_id, set()))

        for queue in subscribers:
            await queue.put(event)

    async def subscribe(self, workflow_id: str) -> AsyncIterator[WorkflowEvent]:
        """Yield historical and future events for a workflow."""
        queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue()

        async with self._lock:
            historical_events = list(self._history.get(workflow_id, []))
            terminal_seen = any(
                event.event in TERMINAL_WORKFLOW_EVENTS for event in historical_events
            )
            if not terminal_seen:
                self._subscribers[workflow_id].add(queue)

        try:
            for event in historical_events:
                yield event
                if event.event in TERMINAL_WORKFLOW_EVENTS:
                    return

            while True:
                event = await queue.get()
                yield event
                if event.event in TERMINAL_WORKFLOW_EVENTS:
                    return
        finally:
            async with self._lock:
                subscribers = self._subscribers.get(workflow_id)
                if subscribers is not None:
                    subscribers.discard(queue)
                    if not subscribers:
                        self._subscribers.pop(workflow_id, None)


def format_sse(event: WorkflowEvent) -> str:
    """Format a workflow event as a Server-Sent Events frame."""
    lines = [
        f"event: {event.event.value}",
        f"id: {event.id}",
        f"data: {event.model_dump_json()}",
    ]
    return "\n".join(lines) + "\n\n"


workflow_event_bus = WorkflowEventBus()


__all__ = ["WorkflowEventBus", "format_sse", "workflow_event_bus"]
