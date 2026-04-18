# EnduraSync

EnduraSync is a private WHOOP-integrated training dashboard. It is built as a single-repo modular monolith with a React + TypeScript + Vite frontend, a FastAPI backend, SQLite, SQLAlchemy, and Alembic.

The source of truth for product scope and sequencing is `BUILD_PLAN.md`.

## Local Development

1. Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

2. Install backend dependencies in `backend/.venv`:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ..
```

3. Install frontend dependencies:

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

The backend serves health checks at:

- `http://localhost:8000/health`
- `http://localhost:8000/api/v1/health`

The frontend dev server runs at `http://localhost:5173`.

## Command Contract

The root `Makefile` defines the commands later phases should preserve:

- `make backend-dev`
- `make frontend-dev`
- `make test`
- `make lint`
- `make format`
- `make migrate`
- `make seed`
- `make integrity`
- `make build`

## Privacy Posture

Version 1 targets Docker Compose on a Tailscale-only private server. WHOOP tokens, raw provider payloads, and AI provider secrets must remain server-side. AI is disabled by default and, when added later, will use derived metrics plus optional athlete profile context rather than WHOOP tokens or raw payloads.
