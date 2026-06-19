# Agent Orchestration Dashboard

A full-stack dashboard that runs a task through a sequence of specialized AI agents, persists the workflow, and streams live progress to a React interface.

This repository is built as a software engineering portfolio project. It demonstrates backend orchestration, API design, persistence, real-time updates, frontend data flows, Docker-based development, and testable service boundaries.

## Highlights

- FastAPI backend with a sequential multi-agent orchestration service.
- React + TypeScript dashboard for running workflows and reviewing saved results.
- Live workflow updates with Server-Sent Events.
- React Flow visualization for agent status and execution order.
- SQLite persistence with SQLAlchemy repository layer.
- OpenRouter-compatible model client with mocked tests.
- Docker Compose setup for CPU-only development.
- Backend pytest suite covering agents, orchestration, persistence, SSE events, and API contract.
- Frontend Vitest, ESLint, and Prettier setup.
- Ruff linting and formatting for Python.
- Makefile shortcuts for common development tasks.

## Demo Flow

```text
User submits a task
  |
  v
Planner Agent
  |
  v
Research Agent
  |
  v
Technical Architect Agent
  |
  v
Developer Agent
  |
  v
Reviewer Agent
  |
  v
Final Answer Agent
  |
  v
Saved workflow + live dashboard updates
```

Each agent receives the original task plus the outputs from previous agents. The frontend opens an SSE connection before submitting the workflow, so the graph and result cards update while the backend is still running.

## Screenshots

Add screenshots after running the project locally:

```text
docs/screenshots/dashboard.png        # Health status and project overview
docs/screenshots/workflow-run.png     # Live multi-agent workflow run
docs/screenshots/workflow-detail.png  # Saved workflow detail page
docs/screenshots/history.png          # Workflow history
```

## Architecture

```text
React + TypeScript Dashboard (Vite)
  |  POST /api/workflows/run
  |  GET  /api/workflows/{workflow_id}/events
  v
FastAPI Backend
  |
  +--> SequentialOrchestrator
  |      +--> Planner -> Researcher -> Architect -> Developer -> Reviewer -> Final Answer
  |              |
  |              v
  |          OpenRouter-compatible chat completion API
  |
  +--> WorkflowEventBus -> Server-Sent Events -> React Flow UI
  |
  +--> WorkflowRepository -> SQLite workflow_runs + agent_execution_steps
```

More detail: [docs/architecture.md](docs/architecture.md)

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

## Quick Start With Docker

Prerequisites:

- Docker and Docker Compose
- OpenRouter API key for live model calls

Create a local environment file:

```bash
cp .env.example .env
```

Build and run both services:

```bash
docker compose build
docker compose up
```

Open:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Run one service:

```bash
docker compose up backend
docker compose up frontend
```

The Docker setup uses CPU-friendly defaults and does not require a GPU.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend expects the backend at `http://localhost:8000` unless `VITE_API_BASE_URL` is changed.

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

### Docker Compose `.env`

| Variable | Default or example | Description |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | empty | Required for live model calls; tests and static UI work without it. |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model routed through OpenRouter. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter-compatible API base URL. |
| `OPENROUTER_TIMEOUT_SECONDS` | `60` | HTTP timeout for model calls. |
| `DATABASE_URL` | `sqlite:////data/orchestration.db` | SQLite path inside Docker. |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` | Allowed frontend origins. |
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
| `POST` | `/api/agents/planner/run` | Run the planner agent only. |
| `POST` | `/api/workflows/run` | Run the complete sequential workflow. |
| `GET` | `/api/workflows` | List persisted workflow runs. |
| `GET` | `/api/workflows/{workflow_id}` | Read one workflow with all agent steps. |
| `GET` | `/api/workflows/{workflow_id}/events` | Stream live workflow events with SSE. |
| `GET` | `/docs` | FastAPI Swagger UI. |
| `GET` | `/openapi.json` | OpenAPI schema. |

Run a workflow:

```bash
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Analyze this startup idea and create a technical implementation plan."}'
```

Run with a client-generated workflow ID for live event subscriptions:

```bash
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "demo-workflow-1", "task": "Design a secure internal AI support tool for a SaaS company."}'
```

Stream live events:

```bash
curl -N http://localhost:8000/api/workflows/demo-workflow-1/events
```

## Sample Tasks

Try these from the Workflow Run page or `POST /api/workflows/run`:

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

The backend tests mock model calls and use temporary SQLite databases, so they do not require a real OpenRouter key or a committed database file.

## Repository Structure

```text
ai-agent-orchestration-dashboard/
  backend/
    app/
      agents/          Role-specific agent classes
      api/             FastAPI routers
      core/            Settings
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
      api/             Axios API helpers
      components/      Layout, UI, workflow components
      hooks/           SSE workflow event hook
      lib/             Display helpers
      pages/           Dashboard, run, history, detail pages
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

## Portfolio Focus

This project is intended to show:

- Clean separation between API routes, services, repositories, and domain models.
- Practical orchestration of multiple model-backed agents.
- Real-time frontend updates without introducing a message broker.
- Testable backend logic with mocked external API calls.
- A development environment that can run locally or in Docker.

## Future Improvements

1. Add parallel and conditional orchestration workflows.
2. Move long-running workflows to a background worker and queue.
3. Add authentication, project workspaces, and team access.
4. Add PostgreSQL support for multi-user deployments.
5. Add model/provider selection in the frontend.
6. Add richer workflow analytics and run comparison views.
7. Add production Docker targets with a built static frontend.
8. Add screenshot assets and a short demo GIF.
