# ADR 0002: Architecture Stack

## Status

Accepted.

ADRs are append-only unless a later ADR explicitly supersedes them.

## Context

The app is private, single-user, and data-heavy enough to need a real backend, migrations, and a polished frontend without SaaS complexity.

## Decision

- Repository shape: single-repo modular monolith.
- Frontend: React, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, and Recharts later.
- Backend: FastAPI, Pydantic v2, SQLAlchemy 2.x, and Alembic.
- Database: SQLite with WAL mode.
- Deployment target: Docker Compose on a Tailscale-only private server.
- Production path later: `~/sites/endurasync`.
- Scheduling later: host cron or systemd timer invoking a backend sync command.
- AI boundary: read-only module consuming derived metrics and optional athlete profile context.

## Consequences

Backend services own calculations and API contracts. The frontend renders backend-derived values and does not reimplement metrics formulas.

