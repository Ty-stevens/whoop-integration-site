# EnduraSync - WHOOP Integration Website

EnduraSync is a WHOOP-connected training intelligence web app that turns recovery, strain, sleep, and workout data into actionable dashboards and trend reporting.

It is built as a modular monolith with:

- Frontend: React, TypeScript, Vite
- Backend: FastAPI, SQLAlchemy, Alembic
- Data store: SQLite (default)
- Deployment target: Docker Compose on a private server

The project planning source of truth is [`BUILD_PLAN.md`](./BUILD_PLAN.md).

## Features

- WHOOP OAuth integration and sync orchestration
- Dashboard views for recovery, strain, training log, and goals
- Six-month reporting and progress views
- Data integrity checks and scheduled sync support
- Optional AI summary pipeline with server-side privacy controls

## Project Structure

```text
backend/    FastAPI API, services, models, migrations, tests
frontend/   React app, routes, shared UI components, tests
deploy/     Docker Compose and deployment templates
docs/       ADRs, architecture notes, runbooks
scripts/    Operational utility scripts
```

## Quick Start (Local Development)

1. Create local environment variables:

```bash
cp .env.example .env.local
```

2. Set up backend dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ..
```

3. Set up frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

4. Run backend and frontend in separate terminals:

```bash
make backend-dev
make frontend-dev
```

5. Open:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/health`
- API health: `http://localhost:8000/api/v1/health`

## Common Commands

The root `Makefile` provides:

- `make backend-dev`
- `make frontend-dev`
- `make test`
- `make lint`
- `make format`
- `make migrate`
- `make seed`
- `make integrity`
- `make build`

## Privacy and Security

WHOOP tokens, provider payloads, and AI provider secrets are kept server-side. AI features are optional and disabled by default in baseline deployments.

## Deployment

See deployment templates in [`deploy/`](./deploy) and runbooks in [`docs/runbooks/`](./docs/runbooks).
