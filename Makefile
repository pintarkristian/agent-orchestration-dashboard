.PHONY: backend-install backend-test backend-lint backend-format frontend-install frontend-dev frontend-test frontend-lint frontend-format docker-up test lint format

backend-install:
	cd backend && python -m pip install -r requirements.txt

backend-test:
	cd backend && python -m pytest

backend-lint:
	cd backend && python -m ruff check .

backend-format:
	cd backend && python -m ruff format .

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-test:
	cd frontend && npm run test

frontend-lint:
	cd frontend && npm run lint

frontend-format:
	cd frontend && npm run format

docker-up:
	docker compose up

test: backend-test frontend-test

lint: backend-lint frontend-lint

format: backend-format frontend-format
