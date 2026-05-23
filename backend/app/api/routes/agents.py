from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.agents.planner_agent import PlannerAgent
from app.models.agent import AgentExecutionResult
from app.services.openrouter_client import OpenRouterClient

router = APIRouter(prefix="/api/agents", tags=["agents"])


class PlannerRunRequest(BaseModel):
    """Request payload for running the planner agent."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task: str = Field(
        ...,
        min_length=1,
        description="User task to break into smaller steps.",
    )


def get_openrouter_client() -> OpenRouterClient:
    """Create the OpenRouter client dependency."""
    return OpenRouterClient()


def get_planner_agent(
    openrouter_client: OpenRouterClient = Depends(get_openrouter_client),
) -> PlannerAgent:
    """Create the planner agent dependency."""
    return PlannerAgent(openrouter_client=openrouter_client)


@router.post("/planner/run", response_model=AgentExecutionResult)
async def run_planner_agent(
    request: PlannerRunRequest,
    planner_agent: PlannerAgent = Depends(get_planner_agent),
) -> AgentExecutionResult:
    """Run the planner agent for a user task."""
    return await planner_agent.run(request.task)
