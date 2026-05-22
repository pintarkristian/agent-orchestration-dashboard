# AI Agent Orchestration Dashboard

**AI Agent Orchestration Dashboard** is a full-stack portfolio project that demonstrates how multiple AI agents can work together to solve complex tasks. The project is built with a **Python FastAPI backend**, **OpenRouter API integration foundation**, and a **React + TypeScript frontend** prepared to visualize the orchestration process.

The goal of this repository is to demonstrate practical skills in **Python development**, **AI API integration**, **multi-agent workflow architecture**, **backend API design**, and **modern frontend development**.

## Project Idea

Instead of sending one prompt to one AI model, this application will eventually run a small team of specialized AI agents. Each agent will have a specific role and contribute part of the final answer.

Example future agents could include:

- **Planner Agent** — breaks the user request into smaller tasks
- **Research Agent** — analyzes context, market, or useful background information
- **Technical Architect Agent** — proposes architecture and technology choices
- **Developer Agent** — writes technical solutions or code
- **Reviewer Agent** — checks the result for quality, bugs, and missing details
- **Final Answer Agent** — combines everything into one clean final response

The backend will coordinate agents, decide execution order, send requests to OpenRouter, store intermediate outputs, and return structured results. The frontend will display the process visually so users can see how the agents work together.

## Repository Structure

```text
ai-agent-orchestration-dashboard/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── agents/          # Base and role-specific AI agents
│   │   ├── api/             # API route modules
│   │   ├── core/            # Configuration and shared settings
│   │   ├── db/              # SQLAlchemy SQLite session and ORM models
│   │   ├── models/          # Pydantic domain models and enums
│   │   ├── repositories/    # Persistence access layer
│   │   ├── schemas/         # Future shared Pydantic schemas
│   │   └── services/        # OpenRouter client and orchestration services
│   ├── tests/               # Pytest test suite
│   ├── .env.example         # Backend environment variable template
│   ├── pyproject.toml       # Python tooling configuration
│   └── requirements.txt     # Backend dependencies
├── frontend/                # React + TypeScript frontend
│   ├── src/
│   │   ├── api/             # Axios API client and workflow API helpers
│   │   ├── components/      # Layout and reusable UI components
│   │   ├── hooks/           # React hooks, including live workflow event streaming
│   │   ├── lib/             # Shared frontend constants
│   │   ├── pages/           # Dashboard, workflow run, history, and detail pages
│   │   ├── styles/          # Tailwind/global styles
│   │   └── types/           # Shared TypeScript types
│   ├── .env.example         # Frontend environment variable template
│   ├── package.json         # Frontend dependencies and scripts
│   ├── tailwind.config.ts   # Tailwind CSS configuration
│   └── vite.config.ts       # Vite configuration
├── docs/                    # Architecture and development notes
├── .gitignore               # Python, Node, build, log, venv, and env ignores
├── LICENSE
└── README.md
```

## Backend Foundation

The backend is prepared for:

- FastAPI
- Pydantic and pydantic-settings
- Async HTTP requests with `httpx`
- OpenRouter API integration foundation
- Base agent plus specialized planner, research, architect, developer, reviewer, and final answer agents
- First Planner Agent endpoint at `/api/agents/planner/run`
- Sequential orchestration endpoint at `/api/workflows/run`
- SQLite persistence with SQLAlchemy for workflow runs and agent steps
- Workflow history endpoints at `/api/workflows` and `/api/workflows/{workflow_id}`
- Server-Sent Events endpoint at `/api/workflows/{workflow_id}/events` for live workflow updates
- Pytest testing

## Docker Development

The application can run in Docker without GPU support. The Docker Compose setup uses a Python slim image for the backend, a Node image for the Vite frontend, bind mounts the source directories for development, and stores SQLite data in a Docker volume.

Create a local Compose environment file if you want to override the defaults:

```bash
cp .env.example .env
```

Important environment variables:

- `OPENROUTER_API_KEY` - optional OpenRouter API key for live model calls
- `OPENROUTER_MODEL` - defaults to `openai/gpt-4o-mini`
- `DATABASE_URL` - defaults to `sqlite:////data/orchestration.db` in Docker
- `VITE_API_BASE_URL` - defaults to `http://localhost:8000`

Build the containers:

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

Run locally:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
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

Run the full sequential workflow endpoint. This saves the workflow run and each agent step to SQLite:

```bash
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Analyze this startup idea and create a technical implementation plan."}'
```


List saved workflow runs:

```bash
curl http://localhost:8000/api/workflows
```

Get one saved workflow run:

```bash
curl http://localhost:8000/api/workflows/<workflow_id>
```

Stream live workflow events for a running workflow:

```bash
curl -N http://localhost:8000/api/workflows/<workflow_id>/events
```

Run tests:

```bash
pytest
```

## Frontend Foundation

The frontend is prepared for:

- React
- TypeScript
- Tailwind CSS
- Axios API client
- TanStack Query
- React Router
- React Flow workflow visualization
- Responsive dashboard layout with reusable UI components
- Workflow run form connected to `POST /api/workflows/run`
- Workflow history page connected to `GET /api/workflows`
- Workflow detail page connected to `GET /api/workflows/{workflow_id}`
- Final answer, live workflow graph, and per-agent step result cards

Run locally:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend runs on `http://localhost:5173` by default and expects the backend API at `http://localhost:8000`. It includes Dashboard, Workflow Run, Workflow History, and Workflow Detail pages. The Workflow Run page submits tasks to `POST /api/workflows/run`, listens to `GET /api/workflows/{workflow_id}/events` for Server-Sent Events, updates the React Flow graph as agents run, shows intermediate outputs as soon as they arrive, and falls back to the final POST response if the live connection fails. The Workflow History page reads saved runs from `GET /api/workflows`, and each detail page reads a saved run from `GET /api/workflows/{workflow_id}` with the same graph and detailed step inspection UI.

## Current Scope

This version contains the clean full-stack foundation, the OpenRouter client, specialized backend agents, the sequential multi-agent workflow orchestration endpoint, SQLite workflow persistence, a functional frontend workflow run UI, responsive saved workflow history/detail screens, React Flow workflow visualization, and Server-Sent Events for real-time workflow status updates.

Planned future work includes:

1. Parallel or conditional orchestration workflows
2. Authentication and project/team workspaces
