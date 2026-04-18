.PHONY: backend-dev frontend-dev test frontend-test lint format migrate seed integrity build

backend-dev:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/pytest
	cd frontend && npm run test

frontend-test:
	cd frontend && npm run test

lint:
	cd backend && .venv/bin/ruff check app tests
	cd frontend && npm run lint

format:
	cd backend && .venv/bin/ruff format app tests
	cd frontend && npm run format

migrate:
	cd backend && .venv/bin/alembic upgrade head

seed:
	cd backend && .venv/bin/python -m app.jobs.seed

integrity:
	cd backend && .venv/bin/python -m app.jobs.check_integrity

build:
	cd frontend && npm run build
	cd backend && .venv/bin/python -m compileall app
