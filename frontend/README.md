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
- Server-Sent Events listener for `GET /api/workflows/{workflow_id}/events`
- Final answer, live workflow graph, and per-agent step result cards
- Saved workflow history and detail pages connected to the backend API
- Clickable agent graph with status-aware nodes and step detail panel

## Pages

- Dashboard: project overview and backend health status
- Workflow Run: task input form, backend workflow submission, live SSE status updates, loading/error states, final answer, workflow graph, and per-agent step cards
- Workflow History: responsive list/table of saved workflow runs from `GET /api/workflows`
- Workflow Detail: saved run detail page powered by `GET /api/workflows/{workflow_id}` with workflow graph, step details, and live event fallback when a run is still active

## Components

- `AppLayout`
- `Header`
- `Sidebar`
- `Card`
- `StatusBadge`
- `LoadingState`
- `ErrorState`
- `WorkflowGraph`
- `useWorkflowEvents` hook

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

## Real-Time Workflow Updates

When a workflow is started from the Workflow Run page, the frontend generates a workflow ID, opens an `EventSource` connection to `GET /api/workflows/{workflow_id}/events`, and then submits the task to `POST /api/workflows/run`. React Flow nodes update as agents move through pending, running, completed, and failed states. If the SSE connection fails, the UI still falls back to the final POST response.
