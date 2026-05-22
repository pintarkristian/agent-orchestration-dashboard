from __future__ import annotations

from app.agents.base_agent import BaseAgent, CompletionClient
from app.models.enums import AgentRole

TECHNICAL_ARCHITECT_SYSTEM_PROMPT = """You are the Technical Architect Agent.
You work inside an AI agent orchestration system.
Your job is to propose a clean architecture and technology choices for the user's task.
Focus on system boundaries, backend/frontend responsibilities, data flow, APIs,
persistence, integrations, scalability, security, and maintainability.
Provide practical recommendations without writing full implementation code."""


class TechnicalArchitectAgent(BaseAgent):
    """Agent that proposes architecture and technology choices."""

    def __init__(self, openrouter_client: CompletionClient) -> None:
        super().__init__(
            role=AgentRole.TECHNICAL_ARCHITECT,
            name="Technical Architect Agent",
            description="Proposes architecture, data flow, and technology choices.",
            system_prompt=TECHNICAL_ARCHITECT_SYSTEM_PROMPT,
            openrouter_client=openrouter_client,
        )
