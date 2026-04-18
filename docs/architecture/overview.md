# Architecture Overview

EnduraSync is a private modular monolith.

The frontend is a React + TypeScript + Vite app with Tailwind CSS, React Router, and TanStack Query. It renders backend-provided metrics and does not calculate training formulas.

The backend is FastAPI with Pydantic settings and schemas, SQLAlchemy, Alembic migrations, and SQLite in WAL mode. Backend services own sync, persistence, goal resolution, metrics, reports, and exports.

Deployment targets Docker Compose on a Tailscale-only private server. The app should not require a public SaaS account model or public internet exposure.

AI is disabled by default. When enabled later, it must consume derived metrics and optional athlete profile context, never WHOOP tokens or raw WHOOP payloads.

