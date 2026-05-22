# Backend

Python FastAPI backend foundation for the AI Agent Orchestration Dashboard.

## Prepared For

- FastAPI application structure
- Pydantic settings, schemas, and core orchestration data models
- Async HTTP requests with `httpx`
- OpenRouter API client foundation
- Base agent plus specialized planner, research, architect, developer, reviewer, and final answer agents
- Simple Planner Agent execution endpoint
- Sequential multi-agent orchestration service and `/api/workflows/run` endpoint
- SQLite persistence with SQLAlchemy for workflow runs and agent steps
- Workflow history endpoints at `/api/workflows` and `/api/workflows/{workflow_id}`
- Server-Sent Events endpoint at `/api/workflows/{workflow_id}/events` for live status updates
- Pytest-based testing

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your OpenRouter values when you are ready to call the API:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TIMEOUT_SECONDS=60
DATABASE_URL=sqlite:///./orchestration.db
```

Run the API:

```bash
python -m uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Run the planner agent endpoint:

```bash
curl -X POST http://localhost:8000/api/agents/planner/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Create an AI agent orchestration dashboard"}'
```

Run the full sequential workflow endpoint. This saves the workflow run and each agent step to SQLite. You can optionally pass a client-generated `workflow_id` so the frontend can subscribe to live events before the POST request finishes:

```bash
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "demo-workflow-1", "task": "Analyze this startup idea and create a technical implementation plan."}'
```


List saved workflow runs:

```bash
curl http://localhost:8000/api/workflows
```

Get one saved workflow run:

```bash
curl http://localhost:8000/api/workflows/<workflow_id>
```

Stream live workflow events while a workflow is running:

```bash
curl -N http://localhost:8000/api/workflows/<workflow_id>/events
```

Run tests:

```bash
pytest
```

The OpenRouter, agent, orchestration, persistence, and SSE event formatting tests use mocks or temporary SQLite databases, so they do not call the real OpenRouter API or require a local database file.
