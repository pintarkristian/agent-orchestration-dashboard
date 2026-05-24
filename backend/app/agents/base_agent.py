from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.models.agent import AgentExecutionResult
from app.models.enums import AgentRole, WorkflowStatus


class CompletionClient(Protocol):
    """Protocol for AI completion clients used by agents."""

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text from a system prompt and user prompt."""


class BaseAgent:
    """Base class for simple AI agents backed by an async completion client."""

    def __init__(
        self,
        *,
        role: AgentRole,
        name: str,
        description: str,
        system_prompt: str,
        openrouter_client: CompletionClient,
    ) -> None:
        self.role = role
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.openrouter_client = openrouter_client

    async def run(self, input_text: str) -> AgentExecutionResult:
        """Run the agent and return a structured execution result."""
        started_at = datetime.now(UTC)

        try:
            output = await self.openrouter_client.generate_completion(
                system_prompt=self.system_prompt,
                user_prompt=input_text,
            )
            completed_at = datetime.now(UTC)

            return AgentExecutionResult(
                role=self.role,
                input=input_text,
                output=output,
                status=WorkflowStatus.COMPLETED,
                error=None,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=self._duration_ms(started_at, completed_at),
            )
        except Exception as exc:
            completed_at = datetime.now(UTC)
            error_message = str(exc) or exc.__class__.__name__

            return AgentExecutionResult(
                role=self.role,
                input=input_text,
                output=None,
                status=WorkflowStatus.FAILED,
                error=error_message,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=self._duration_ms(started_at, completed_at),
            )

    @staticmethod
    def _duration_ms(started_at: datetime, completed_at: datetime) -> int:
        """Return elapsed time in milliseconds."""
        return max(0, int((completed_at - started_at).total_seconds() * 1000))
