from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

from app.api.routes.workflows import get_openrouter_client
from app.db.models import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import AgentRole, WorkflowStatus
from app.models.workflow import WorkflowResult, WorkflowStep
from app.repositories.workflow_repository import WorkflowRepository
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class MockOpenRouterClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return f"Mock output {len(self.calls)}"


def build_test_session(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test_orchestration.db'}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )


def sample_workflow_result() -> WorkflowResult:
    started_at = datetime.now(UTC)
    completed_at = datetime.now(UTC)
    return WorkflowResult(
        id="workflow-test-1",
        input="Analyze a startup idea",
        output="Final response",
        final_answer="Final response",
        status=WorkflowStatus.COMPLETED,
        created_at=started_at,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=10,
        total_duration_ms=10,
        steps=[
            WorkflowStep(
                id="step-test-1",
                role=AgentRole.PLANNER,
                name="Planner Agent",
                description="Breaks the task into smaller steps.",
                input="Original task",
                output="Planner output",
                status=WorkflowStatus.COMPLETED,
                error=None,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=5,
            ),
            WorkflowStep(
                id="step-test-2",
                role=AgentRole.FINAL_ANSWER,
                name="Final Answer Agent",
                description="Combines outputs.",
                input="Previous outputs",
                output="Final response",
                status=WorkflowStatus.COMPLETED,
                error=None,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=5,
            ),
        ],
    )


def test_workflow_repository_saves_and_reads_workflow(tmp_path) -> None:
    TestingSessionLocal = build_test_session(tmp_path)

    with TestingSessionLocal() as db:
        repository = WorkflowRepository(db)
        saved = repository.save_workflow_result(sample_workflow_result())

        assert saved.id == "workflow-test-1"
        assert saved.input == "Analyze a startup idea"
        assert saved.status == WorkflowStatus.COMPLETED
        assert saved.final_answer == "Final response"
        assert len(saved.steps) == 2
        assert saved.steps[0].role == AgentRole.PLANNER
        assert saved.steps[1].role == AgentRole.FINAL_ANSWER

        loaded = repository.get_workflow("workflow-test-1")
        assert loaded is not None
        assert loaded.id == saved.id
        assert loaded.steps[0].output == "Planner output"

        all_workflows = repository.list_workflows()
        assert len(all_workflows) == 1
        assert all_workflows[0].id == saved.id


def test_workflow_routes_persist_runs_and_return_history(tmp_path) -> None:
    TestingSessionLocal = build_test_session(tmp_path)
    mock_openrouter_client = MockOpenRouterClient()

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_openrouter_client] = lambda: mock_openrouter_client

    try:
        with TestClient(app) as client:
            run_response = client.post(
                "/api/workflows/run",
                json={"task": "Analyze this startup idea and create a technical plan."},
            )
            assert run_response.status_code == 200
            workflow = run_response.json()
            workflow_id = workflow["id"]

            assert workflow["status"] == "completed"
            assert workflow["input"] == "Analyze this startup idea and create a technical plan."
            assert workflow["final_answer"] == "Mock output 6"
            assert len(workflow["steps"]) == 6
            assert [step["role"] for step in workflow["steps"]] == [
                "planner",
                "researcher",
                "technical_architect",
                "developer",
                "reviewer",
                "final_answer",
            ]

            list_response = client.get("/api/workflows")
            assert list_response.status_code == 200
            workflows = list_response.json()
            assert len(workflows) == 1
            assert workflows[0]["id"] == workflow_id

            detail_response = client.get(f"/api/workflows/{workflow_id}")
            assert detail_response.status_code == 200
            detail = detail_response.json()
            assert detail["id"] == workflow_id
            assert detail["final_answer"] == "Mock output 6"
            assert len(detail["steps"]) == 6

            missing_response = client.get("/api/workflows/missing-id")
            assert missing_response.status_code == 404
    finally:
        app.dependency_overrides.clear()
