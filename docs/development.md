# Development Notes

This document collects day-to-day commands for working on the project locally.

## Backend

The backend is in `backend/` and uses FastAPI, Pydantic, SQLAlchemy, SQLite, pytest, and Ruff.

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

Run tests and quality checks:

```bash
pytest
ruff check .
ruff format .
```

## Frontend

The frontend is in `frontend/` and uses Vite, React, TypeScript, Tailwind CSS, Axios, TanStack Query, React Flow, Vitest, ESLint, and Prettier.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Run tests and quality checks:

```bash
npm run test
npm run lint
npm run format:check
npm run build
```

## Docker

The root `docker-compose.yml` runs both services for development.

```bash
cp .env.example .env
docker compose build
docker compose up
```

The Compose setup is CPU-friendly and does not require a GPU.

## Root Makefile Shortcuts

```bash
make backend-install
make backend-test
make frontend-install
make frontend-dev
make docker-up
make test
make lint
make format
```

## Environment Files

Copy example files before running locally:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Do not commit real `.env` files, API keys, local database files, or generated build output.
