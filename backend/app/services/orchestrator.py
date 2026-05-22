from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from app.agents import (
    DeveloperAgent,
    FinalAnswerAgent,
    PlannerAgent,
    ResearchAgent,
    ReviewerAgent,
    TechnicalArchitectAgent,
)
from app.agents.base_agent import CompletionClient
from app.models.agent import AgentExecutionResult
from app.models.enums import AgentRole, WorkflowStatus
from app.models.workflow import WorkflowResult, WorkflowStep
from app.models.workflow_event import WorkflowEvent, WorkflowEventType
from app.repositories.workflow_repository import WorkflowRepository


class WorkflowAgent(Protocol):
    """Protocol implemented by orchestration agents."""

    role: AgentRole
    name: str
    description: str

    async def run(self, input_text: str) -> AgentExecutionResult:
        """Run the agent for the supplied input text."""


class WorkflowEventPublisher(Protocol):
    """Protocol implemented by workflow event publishers."""

    async def publish(self, event: WorkflowEvent) -> None:
        """Publish a workflow event."""


class SequentialOrchestrator:
    """Runs all specialized agents in a fixed sequential workflow."""

    def __init__(
        self,
        *,
        openrouter_client: CompletionClient | None = None,
        agents: list[WorkflowAgent] | None = None,
        workflow_repository: WorkflowRepository | None = None,
        event_publisher: WorkflowEventPublisher | None = None,
    ) -> None:
        self.workflow_repository = workflow_repository
        self.event_publisher = event_publisher
        if agents is not None:
            self.agents = agents
        else:
            if openrouter_client is None:
                raise ValueError("openrouter_client is required when agents are not provided")
            self.agents = self._build_default_agents(openrouter_client)

    async def run(self, task: str, workflow_id: str | None = None) -> WorkflowResult:
        """Run the user task through all agents in sequence."""
        workflow_id = workflow_id or str(uuid4())
        workflow_started_at = datetime.now(UTC)
        steps: list[WorkflowStep] = []
        previous_outputs: list[WorkflowStep] = []
        pending_steps = [self._pending_step(agent=agent) for agent in self.agents]
        final_answer: str | None = None

        await self._publish(
            WorkflowEvent(
                workflow_id=workflow_id,
                event=WorkflowEventType.WORKFLOW_STARTED,
                status=WorkflowStatus.RUNNING,
                workflow=WorkflowResult(
                    id=workflow_id,
                    input=task,
                    output=None,
                    final_answer=None,
                    status=WorkflowStatus.RUNNING,
                    steps=pending_steps,
                    error=None,
                    created_at=workflow_started_at,
                    started_at=workflow_started_at,
                    completed_at=None,
                    duration_ms=None,
                    total_duration_ms=None,
                ),
                message="Workflow started.",
            )
        )

        for pending_step in pending_steps:
            await self._publish(
                WorkflowEvent(
                    workflow_id=workflow_id,
                    event=WorkflowEventType.AGENT_PENDING,
                    status=WorkflowStatus.PENDING,
                    role=pending_step.role,
                    step=pending_step,
                    message=f"{pending_step.name} is pending.",
                )
            )

        for agent in self.agents:
            agent_input = self._build_agent_input(
                task=task,
                current_role=agent.role,
                previous_steps=previous_outputs,
            )
            running_step = self._running_step(agent=agent, input_text=agent_input)
            await self._publish(
                WorkflowEvent(
                    workflow_id=workflow_id,
                    event=WorkflowEventType.AGENT_RUNNING,
                    status=WorkflowStatus.RUNNING,
                    role=agent.role,
                    step=running_step,
                    message=f"{agent.name} is running.",
                )
            )

            result = await agent.run(agent_input)
            step = self._step_from_result(agent=agent, result=result, step_id=running_step.id)
            steps.append(step)

            if result.status == WorkflowStatus.FAILED:
                await self._publish(
                    WorkflowEvent(
                        workflow_id=workflow_id,
                        event=WorkflowEventType.AGENT_FAILED,
                        status=WorkflowStatus.FAILED,
                        role=agent.role,
                        step=step,
                        message=f"{agent.name} failed.",
                    )
                )

                workflow_completed_at = datetime.now(UTC)
                workflow_error = self._workflow_error(agent=agent, result=result)
                duration_ms = self._duration_ms(workflow_started_at, workflow_completed_at)

                failed_result = WorkflowResult(
                    id=workflow_id,
                    input=task,
                    output=None,
                    final_answer=None,
                    status=WorkflowStatus.FAILED,
                    steps=steps,
                    error=workflow_error,
                    created_at=workflow_started_at,
                    started_at=workflow_started_at,
                    completed_at=workflow_completed_at,
                    duration_ms=duration_ms,
                    total_duration_ms=duration_ms,
                )
                persisted_result = self._persist_result(failed_result)
                await self._publish(
                    WorkflowEvent(
                        workflow_id=workflow_id,
                        event=WorkflowEventType.WORKFLOW_FAILED,
                        status=WorkflowStatus.FAILED,
                        workflow=persisted_result,
                        message=workflow_error,
                    )
                )
                return persisted_result

            await self._publish(
                WorkflowEvent(
                    workflow_id=workflow_id,
                    event=WorkflowEventType.AGENT_COMPLETED,
                    status=WorkflowStatus.COMPLETED,
                    role=agent.role,
                    step=step,
                    message=f"{agent.name} completed.",
                )
            )

            previous_outputs.append(step)
            if agent.role == AgentRole.FINAL_ANSWER:
                final_answer = str(result.output) if result.output is not None else None

        workflow_completed_at = datetime.now(UTC)
        total_duration_ms = self._duration_ms(workflow_started_at, workflow_completed_at)

        completed_result = WorkflowResult(
            id=workflow_id,
            input=task,
            output=final_answer,
            final_answer=final_answer,
            status=WorkflowStatus.COMPLETED,
            steps=steps,
            error=None,
            created_at=workflow_started_at,
            started_at=workflow_started_at,
            completed_at=workflow_completed_at,
            duration_ms=total_duration_ms,
            total_duration_ms=total_duration_ms,
        )
        persisted_result = self._persist_result(completed_result)
        await self._publish(
            WorkflowEvent(
                workflow_id=workflow_id,
                event=WorkflowEventType.WORKFLOW_COMPLETED,
                status=WorkflowStatus.COMPLETED,
                workflow=persisted_result,
                message="Workflow completed.",
            )
        )
        return persisted_result

    def _persist_result(self, result: WorkflowResult) -> WorkflowResult:
        """Persist a workflow result when a repository was provided."""
        if self.workflow_repository is None:
            return result
        return self.workflow_repository.save_workflow_result(result)

    async def _publish(self, event: WorkflowEvent) -> None:
        """Publish a workflow event when live updates are enabled."""
        if self.event_publisher is not None:
            await self.event_publisher.publish(event)

    @staticmethod
    def _build_default_agents(openrouter_client: CompletionClient) -> list[WorkflowAgent]:
        """Create the default agent sequence for a workflow run."""
        return [
            PlannerAgent(openrouter_client=openrouter_client),
            ResearchAgent(openrouter_client=openrouter_client),
            TechnicalArchitectAgent(openrouter_client=openrouter_client),
            DeveloperAgent(openrouter_client=openrouter_client),
            ReviewerAgent(openrouter_client=openrouter_client),
            FinalAnswerAgent(openrouter_client=openrouter_client),
        ]

    @staticmethod
    def _build_agent_input(
        *,
        task: str,
        current_role: AgentRole,
        previous_steps: list[WorkflowStep],
    ) -> str:
        """Build contextual input for the next agent."""
        if not previous_steps:
            return f"Original user task:\n{task}"

        previous_context = "\n\n".join(
            f"{step.role.value} output:\n{step.output}"
            for step in previous_steps
            if step.output is not None
        )

        return (
            f"Original user task:\n{task}\n\n"
            f"Previous agent outputs:\n{previous_context}\n\n"
            f"Now perform the {current_role.value} agent responsibility."
        )

    @staticmethod
    def _pending_step(*, agent: WorkflowAgent) -> WorkflowStep:
        """Create a pending step placeholder for live UI updates."""
        return WorkflowStep(
            role=agent.role,
            name=agent.name,
            description=agent.description,
            input=None,
            output=None,
            status=WorkflowStatus.PENDING,
            error=None,
            created_at=datetime.now(UTC),
            started_at=None,
            completed_at=None,
            duration_ms=None,
        )

    @staticmethod
    def _running_step(*, agent: WorkflowAgent, input_text: str) -> WorkflowStep:
        """Create a running step event payload before an agent completes."""
        now = datetime.now(UTC)
        return WorkflowStep(
            role=agent.role,
            name=agent.name,
            description=agent.description,
            input=input_text,
            output=None,
            status=WorkflowStatus.RUNNING,
            error=None,
            created_at=now,
            started_at=now,
            completed_at=None,
            duration_ms=None,
        )

    @staticmethod
    def _step_from_result(
        *,
        agent: WorkflowAgent,
        result: AgentExecutionResult,
        step_id: str | None = None,
    ) -> WorkflowStep:
        """Convert an agent execution result into a workflow step."""
        return WorkflowStep(
            id=step_id or result.id,
            role=agent.role,
            name=agent.name,
            description=agent.description,
            input=result.input,
            output=result.output,
            status=result.status,
            error=result.error,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_ms=result.duration_ms,
        )

    @staticmethod
    def _workflow_error(*, agent: WorkflowAgent, result: AgentExecutionResult) -> str:
        """Build a useful workflow-level error message."""
        detail = result.error or "Unknown agent error"
        return f"Workflow stopped because {agent.name} failed: {detail}"

    @staticmethod
    def _duration_ms(started_at: datetime, completed_at: datetime) -> int:
        """Return elapsed time in milliseconds."""
        return max(0, int((completed_at - started_at).total_seconds() * 1000))


__all__ = ["SequentialOrchestrator", "WorkflowAgent", "WorkflowEventPublisher"]
