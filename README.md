# AI Agent Orchestration Dashboard

AI Agent Orchestration Dashboard is a full-stack software engineering portfolio project that demonstrates how a backend can coordinate multiple specialized AI agents and stream their progress to a modern frontend dashboard.

The application uses a FastAPI backend, a React + TypeScript frontend, OpenRouter-compatible model calls, SQLite persistence, Server-Sent Events, and Docker-based development setup. It is designed to run on CPU-only environments and does not require GPU support.

## Project Overview

Instead of sending a task to one model and waiting for one answer, this project models a small sequential agent team:

1. Planner Agent breaks down the request.
2. Research Agent adds context and constraints.
3. Technical Architect Agent proposes structure and technology choices.
4. Developer Agent turns the plan into implementation guidance.
5. Reviewer Agent checks the result for gaps and risks.
6. Final Answer Agent combines the work into a clean response.

The backend owns orchestration, persistence, model integration, and live event streaming. The frontend provides the workflow launch screen, run history, detail views, status cards, and graph visualization.

## Architecture Diagram

```text
User
  |
  v
React + TypeScript Dashboard (Vite)
  |  POST /api/workflows/run
  |  GET  /api/workflows/{id}/events
  v
FastAPI Backend
  |
  +--> SequentialOrchestrator
  |      |
  |      +--> Planner -> Researcher -> Architect -> Developer -> Reviewer -> Final Answer
  |              |
  |              v
  |          OpenRouter-compatible chat completion API
  |
  +--> WorkflowEventBus -> Server-Sent Events -> React Flow UI
  |
  +--> WorkflowRepository -> SQLite workflow_runs + agent_execution_steps
```

## Features

- Sequential multi-agent workflow orchestration.
- Specialized agent roles with dedicated prompts and responsibilities.
- OpenRouter API client abstraction.
- FastAPI endpoints for health checks, planner runs, workflow runs, history, detail, and live events.
- SQLite persistence for workflow runs and per-agent execution steps.
- Server-Sent Events for real-time workflow status updates.
- React dashboard with workflow run form, history, detail view, and React Flow graph.
- Docker Compose development environment with backend and frontend bind mounts.
- Backend pytest suite covering agents, orchestration, persistence, events, models, and API contract.
- Frontend Vitest coverage for display helpers.
- Ruff configuration for Python linting and formatting.
- ESLint and Prettier configuration for frontend quality checks.
- Makefile task shortcuts for common local workflows.

## Tech Stack

| Area | Technology |
| --- | --- |
| Backend API | Python 3.11+, FastAPI, Uvicorn |
| Backend models | Pydantic, pydantic-settings |
| Persistence | SQLAlchemy, SQLite |
| AI integration | OpenRouter-compatible HTTP API, httpx |
| Live updates | Server-Sent Events |
| Frontend | React 18, TypeScript, Vite |
| Frontend data | Axios, TanStack Query |
| Visualization | React Flow |
| Styling | Tailwind CSS |
| Backend tests | pytest, pytest-asyncio, FastAPI TestClient |
| Frontend tests | Vitest |
| Quality tools | Ruff, ESLint, Prettier |
| DevOps | Docker, Docker Compose, Makefile |

## Screenshots

Screenshots can be added after running the app locally:

```text
docs/screenshots/dashboard.png        # Dashboard overview
docs/screenshots/workflow-run.png     # Live workflow execution
docs/screenshots/workflow-detail.png  # Saved workflow detail view
docs/screenshots/history.png          # Workflow history
```

Suggested portfolio captions:

- Dashboard overview with backend health status.
- Live multi-agent workflow graph while agents run.
- Final answer and per-agent reasoning cards.
- Persisted workflow history and detail pages.

## Repository Structure

```text
ai-agent-orchestration-dashboard/
  backend/
    app/
      agents/          Specialized agent implementations
      api/             FastAPI routers and route handlers
      core/            Settings and configuration
      db/              SQLAlchemy session and ORM models
      models/          Pydantic domain models
      repositories/    Persistence access layer
      services/        OpenRouter client, orchestrator, event bus
    tests/             pytest suite
    Dockerfile
    pyproject.toml
    requirements.txt
  frontend/
    src/
      api/             Axios client and workflow API helpers
      components/      Layout, UI, and workflow graph components
      hooks/           Live workflow event hook
      lib/             Display helpers and navigation constants
      pages/           Dashboard, run, history, and detail pages
      types/           TypeScript workflow types
    Dockerfile
    package.json
  docs/
    architecture.md
    development.md
  docker-compose.yml
  Makefile
  README.md
```

## Setup Instructions

### Option 1: Docker Compose

Create a local environment file if you want to override defaults:

```bash
cp .env.example .env
```

Build images:

```bash
docker compose build
```

Run the full application:

```bash
docker compose up
```

Run only the backend:

```bash
docker compose up backend
```

Run only the frontend:

```bash
docker compose up frontend
```

Backend: `http://localhost:8000`

Frontend: `http://localhost:5173`

### Option 2: Local Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Option 3: Local Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend expects the backend API at `http://localhost:8000` by default.

## Makefile Commands

```bash
make backend-install
make backend-test
make frontend-install
make frontend-dev
make docker-up
```

Additional quality commands:

```bash
make backend-lint
make backend-format
make frontend-test
make frontend-lint
make frontend-format
make test
make lint
make format
```

## Environment Variables

### Root Docker Compose `.env`

| Variable | Example | Description |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | `sk-or-...` | Optional API key for live model calls. |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model routed through OpenRouter. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter-compatible API base URL. |
| `OPENROUTER_TIMEOUT_SECONDS` | `60` | HTTP timeout for model calls. |
| `DATABASE_URL` | `sqlite:////data/orchestration.db` | SQLite database location inside Docker. |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:5173"]` | Allowed frontend origins. |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Browser-facing backend URL. |

### Backend `backend/.env`

```env
APP_NAME="AI Agent Orchestration Dashboard API"
APP_VERSION="0.1.0"
ENVIRONMENT="development"
OPENROUTER_API_KEY=
OPENROUTER_MODEL="openai/gpt-4o-mini"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
OPENROUTER_TIMEOUT_SECONDS=60
DATABASE_URL="sqlite:///./orchestration.db"
CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

### Frontend `frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | API health, version, and environment metadata. |
| `POST` | `/api/agents/planner/run` | Run only the planner agent for a task. |
| `POST` | `/api/workflows/run` | Run the complete sequential multi-agent workflow. |
| `GET` | `/api/workflows` | List persisted workflow runs. |
| `GET` | `/api/workflows/{workflow_id}` | Read one persisted workflow run with steps. |
| `GET` | `/api/workflows/{workflow_id}/events` | Stream live workflow events with Server-Sent Events. |
| `GET` | `/openapi.json` | OpenAPI schema generated by FastAPI. |
| `GET` | `/docs` | Interactive Swagger UI generated by FastAPI. |

Run a full workflow:

```bash
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Analyze this startup idea and create a technical implementation plan."}'
```

Run a workflow with a client-generated ID for live event subscriptions:

```bash
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "demo-workflow-1", "task": "Design a secure internal AI support tool for a SaaS company."}'
```

Stream workflow events:

```bash
curl -N http://localhost:8000/api/workflows/demo-workflow-1/events
```

## Sample Tasks To Try

Use these in the Workflow Run page or with `POST /api/workflows/run`:

- `Analyze a B2B SaaS idea for AI-powered customer onboarding and create a technical implementation plan.`
- `Design an internal support dashboard that summarizes customer tickets and routes escalations to specialists.`
- `Create a product and engineering plan for a lightweight AI coding assistant for small teams.`
- `Review this architecture idea: a FastAPI backend, React dashboard, SQLite persistence, and background worker queue.`
- `Turn a rough startup idea into requirements, architecture, risks, and an MVP delivery plan.`

## Testing And Quality

Backend:

```bash
cd backend
pytest
ruff check .
ruff format .
```

Frontend:

```bash
cd frontend
npm run test
npm run lint
npm run format:check
npm run build
```

The backend tests mock model calls and use temporary SQLite databases where needed, so they do not require a real OpenRouter key or a committed local database file.

## Docker Notes

- Backend image: Python slim.
- Frontend image: Node slim.
- Backend port: `8000`.
- Frontend port: `5173`.
- Source code is bind-mounted for development.
- `backend_data` stores Docker SQLite data.
- `frontend_node_modules` keeps container dependencies separate from the host.
- `CUDA_VISIBLE_DEVICES` is set to an empty value for a CPU-friendly default.

## Future Improvements

1. Add parallel or conditional orchestration workflows.
2. Add authentication and project/team workspaces.
3. Add background job processing for long-running workflows.
4. Add richer workflow analytics and run comparison views.
5. Add model/provider selection in the frontend.
6. Add production Docker targets with a built static frontend.
7. Add screenshot assets and an animated demo GIF for the portfolio README.
