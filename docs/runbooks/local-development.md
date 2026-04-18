# Local Development Runbook

## First-time setup

```bash
cd /path/to/endurasync
cp .env.example .env.local
```

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Health checks:

- `http://localhost:8000/health`
- `http://localhost:8000/api/v1/health`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Root Commands

Use the root `Makefile` for common workflows from the repository root:

```bash
make backend-dev
make frontend-dev
make test
make lint
make format
make migrate
make seed
make integrity
make build
```

Recommended local verification order before push:

```bash
make lint
make build
make integrity
make test
```

See the deployment runbooks in `docs/runbooks/` for the private Compose stack and backup flow.
