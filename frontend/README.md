# Frontend

React + TypeScript frontend for the AI Agent Orchestration Dashboard.

## Included

- Vite React application
- TypeScript
- Tailwind CSS
- Axios API client
- TanStack Query provider
- React Router pages
- React Flow workflow visualization for workflow run and detail pages
- Clean responsive dashboard layout
- Workflow run form connected to `POST /api/workflows/run`
- Final answer, workflow graph, and per-agent step result cards
- Saved workflow history and detail pages connected to the backend API
- Clickable agent graph with status-aware nodes and step detail panel

## Pages

- Dashboard: project overview and backend health status
- Workflow Run: task input form, backend workflow submission, loading/error states, final answer, workflow graph, and per-agent step cards
- Workflow History: responsive list/table of saved workflow runs from `GET /api/workflows`
- Workflow Detail: saved run detail page powered by `GET /api/workflows/{workflow_id}` with workflow graph and step details

## Components

- `AppLayout`
- `Header`
- `Sidebar`
- `Card`
- `StatusBadge`
- `LoadingState`
- `ErrorState`
- `WorkflowGraph`

## Local Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Production build:

```bash
npm run build
npm run preview
```

The frontend expects the backend API at `http://localhost:8000` by default. Start the backend first with:

```bash
cd backend
python -m uvicorn app.main:app --reload
```
