# WHOOP Training Dashboard Build Plan

This plan turns the product foundation and technical architecture documents into an execution roadmap for building a private WHOOP-integrated training dashboard from an empty repo.

The project goal is not to mirror WHOOP. The project goal is to build a private, polished training control center that answers: what have I done this week, what remains against my targets, and is my recovery keeping pace with training load over time?

Use this file as the command map for future work. Later, you should be able to say `start with P1`, `continue with P2`, or `do P5-B3`, and we can execute that block without re-planning the whole product.

## Source Documents

The plan is based on:

- `../Whoop Training Dashboard Foundation.pdf`
- `../whoop_technical_architecture_foundation.docx`

## Product Definition

A private, visually polished training dashboard that transforms WHOOP workout, sleep, and recovery data into adjustable weekly progress tracking, long-term reporting, and recovery/strain interpretation.

Working product name: `EnduraSync`. This is a placeholder name and can be changed later.

Visual direction: Garmin-inspired dark tactical training dashboard, with high-clarity charts, strong signal colors, and a private command-center feel.

## Version 1 Scope

Version 1 includes:

- Private single-user website.
- WHOOP OAuth connection.
- Server-side token handling with refresh token support.
- Workout, sleep, and recovery ingestion.
- Canonical local storage in SQLite.
- Manual refresh.
- Optional scheduled sync once or twice daily.
- Weekly HR-zone aggregation.
- Adjustable weekly goals per HR zone.
- Cardio and strength session targets.
- Current-week progress and remaining-volume dashboard.
- Recovery and strain trends.
- Monthly summaries.
- 6-month report page.
- CSV export.
- Desktop-first polished UI.
- Dark-mode-first visual direction.
- Private deployment posture behind Tailscale or equivalent.

Version 1 intentionally excludes:

- Public SaaS accounts.
- Multi-user roles.
- Mobile-first design.
- Complex training calendar programming.
- Webhooks as the primary sync mechanism.
- AI-generated coaching as a core dependency.
- Styled PDF export as a required launch feature.
- Advanced wearable integrations beyond WHOOP.

AI intent:

- The app should eventually use OpenClaw or a ChatGPT/OpenAI-compatible provider to generate weekly goal recommendations and training feedback from derived metrics.
- Version 1 should still work without AI so the dashboard, sync, goals, and reports are not blocked by provider setup.
- The first AI version should generate proposed weekly goals for user approval. Fully automatic weekly goal changes can be added later after the recommendation quality is trusted.

## Chosen Architecture

Use a single-repo modular monolith:

- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui-style primitives, TanStack Query, React Router, Recharts.
- Backend: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic.
- Database: SQLite in WAL mode.
- Scheduling: host cron or systemd timer invoking a backend sync command.
- Deployment: one private server, Tailscale-protected, one app container plus persistent SQLite volume.
- AI boundary: future read-only interpretation module that consumes derived metric datasets, not raw WHOOP clients or token state.

## Core Engineering Principles

- Imported WHOOP records are canonical facts.
- User annotations and goal preferences are overlays, not mutations of imported facts.
- Metrics are derived outputs computed from canonical facts and goals.
- Weekly goals are time-versioned, never overwritten in place.
- Sync must be idempotent and safe to re-run.
- Sync uses overlapping lookback windows because WHOOP records can change after first import.
- ISO weeks with Monday start are the single week definition across backend, frontend, reports, and exports.
- Durations are stored in seconds and formatted into minutes only at API/UI boundaries.
- Backend owns domain calculations; frontend should not re-implement metric formulas.
- UI and export numbers must come from the same metrics services.
- The app is private by default and should avoid unnecessary public attack surface.

## Phase Map

- `P0`: Product decisions and repo operating rules.
- `P1`: Repository foundation and local development shell.
- `P2`: Backend foundation, config, database, and migrations.
- `P3`: Frontend foundation and visual design system.
- `P4`: WHOOP OAuth connection and secure token lifecycle.
- `P5`: Canonical data schema and persistence repositories.
- `P6`: WHOOP client, transformers, and sync engine.
- `P7`: Goal profiles, settings, and effective-date logic.
- `P8`: Metrics engine and report dataset builder.
- `P9`: Backend API contracts and typed frontend client.
- `P10`: Dashboard home page and manual refresh UX.
- `P11`: Goals and settings frontend.
- `P12`: Recovery and strain insights frontend.
- `P13`: 6-month report page and CSV export.
- `P14`: Testing, data integrity, and reliability hardening.
- `P15`: Deployment, scheduled sync, backups, and runbooks.
- `P16`: UX polish, empty states, responsive pass, and launch checklist.
- `P17`: Version 1.5 expansion: tags, notes, strength splits.
- `P18`: Future AI interpretation layer and integration handoff.

## Implementation Status Snapshot

Last updated: 2026-04-17.

- `P0`: Implemented.
- `P1`: Implemented.
- `P2`: Implemented.
- `P3`: Implemented as frontend foundation and visual system.
- `P4`: Implemented for the current connection lifecycle. OAuth routes, state validation, token exchange boundary, encrypted token storage, connection table, status, disconnect, Settings UI states, proactive token refresh, retry-after-401, and refresh failure state transitions exist.
- `P5`: Implemented. Canonical fact models, overlay/audit models, Alembic migration, repositories, and repository tests exist.
- `P6`: Implemented for local/manual sync surfaces. Real WHOOP smoke testing with live credentials remains a launch/manual gate.
- `P7`: Implemented. Goal profile effective-date behavior, goal APIs, idempotent default seeding, app settings, and athlete profile persistence exist.
- `P8`: Implemented for Version 1 local gates. Current-week metrics, recovery/strain trends, rolling comparison cards, six-month report dataset, consistency summary, and CSV-backed report dataset exist.
- `P9`: Implemented for Version 1 local gates. Health, WHOOP, sync, settings, athlete profile, goals, dashboard, recovery/strain, report, CSV, workouts, annotation, strength overview, and AI routes exist with maintained frontend TypeScript types.
- `P10`: Implemented. Dashboard uses backend current-week metrics and sync status/run APIs, including manual refresh states.
- `P11`: Implemented. Settings remains functional; Goals page supports editable versioned profiles and history.
- `P12`: Implemented. Recovery and strain page renders backend trend datasets, rolling comparisons, deterministic interpretation, and empty states.
- `P13`: Implemented. Six-month report page uses the backend report dataset and CSV export endpoint.
- `P14`: Implemented for Version 1 local gates. Backend tests cover metrics, APIs, CSV, sync, persistence, OAuth, and integrity checks; frontend Vitest coverage exists for dashboard, goals, and report rendering. Full live E2E remains a manual launch gate.
- `P15`: Implemented for local deployment planning. Docker Compose artifacts, backup script, scheduled sync example, integrity command, and runbooks exist. Real server deployment/restore validation remains a manual launch gate.
- `P16`: Implemented for local gates. Placeholder UI has been removed from core pages, empty states are improved, responsive/accessibility basics are covered, and launch checklist exists.
- `P17`: Implemented. Recent workouts API, annotation update API, Training Log UI, manual classification/tag/notes/strength split editing, and strength overview metrics exist.
- `P18`: Implemented for disabled-by-default/local gates. AI status, context builder, provider adapter boundary, OpenAI-compatible request adapter, dashboard summary panel, Settings status, and draft-only goal suggestions exist. Real provider hookup/smoke testing remains a manual launch gate.

## Global Definition of Done

The project is complete through Version 1 when:

- The app boots locally from documented commands.
- The backend health endpoint works.
- The frontend loads and routes correctly.
- WHOOP OAuth connection works end-to-end.
- Tokens are stored encrypted server-side.
- Initial backfill imports workouts, sleeps, and recoveries.
- Repeated syncs are idempotent.
- Updated provider records update local canonical rows.
- Weekly goals can be edited without code changes.
- Historical goal truth is preserved.
- Dashboard shows current-week zone totals, targets, percent complete, and remaining minutes.
- Dashboard shows cardio and strength session progress.
- Dashboard shows sync status and last successful sync time.
- Recovery and strain trend pages render from backend datasets.
- 6-month report page renders from the shared report dataset builder.
- CSV export matches report-page numbers.
- Basic unit, integration, and end-to-end tests pass.
- The app can be deployed privately on the server.
- SQLite backups are automated and restore steps are documented.
- Production deployment has a documented update, rollback, smoke-test, log, disk-space, and scheduled-sync check process.
- Secrets are not committed.
- The user can access one private URL and use the dashboard repeatedly without developer intervention.
- The AI integration point is documented even if AI is not enabled for Version 1.

---

# P0: Product Decisions and Repo Operating Rules

Implementation status: **Implemented on 2026-04-14.** ADRs, glossary, and classification rules exist under `docs/`.

## Goal

Resolve the few product choices that affect schema, UI copy, and default behavior before writing application code.

## Dependencies

None.

## Outputs

- A short decision log in `docs/adr/`.
- A clear set of defaults for backfill, goals, export, sync, and access.
- A product glossary used by backend and frontend.

## P0-B1: Create Decision Log Structure

Implementation status: **Implemented.** `docs/adr/0001-product-defaults.md`, `0002-architecture-stack.md`, `0003-week-and-time-model.md`, and `docs/glossary.md` exist.

Steps:

1. Create `docs/adr/`.
2. Create `docs/adr/0001-product-defaults.md`.
3. Create `docs/adr/0002-architecture-stack.md`.
4. Create `docs/adr/0003-week-and-time-model.md`.
5. Create `docs/glossary.md`.
6. Add a short note that ADRs are append-only unless a later ADR supersedes them.

Acceptance criteria:

- ADR files exist.
- Each ADR has `Status`, `Context`, `Decision`, and `Consequences` sections.
- The glossary defines `canonical facts`, `goal profile`, `sync run`, `ISO week`, `zone progress`, `remaining volume`, `current week`, `6-month report`, `cardio session`, and `strength session`.

## P0-B2: Decide Version 1 Defaults

Implementation status: **Implemented.** Defaults are recorded in `docs/adr/0001-product-defaults.md`, including EnduraSync name, 180-day backfill, ISO weeks, CSV export, auto-sync off, Tailscale-only access, training defaults, and AI disabled by default.

Recommended defaults:

1. Initial backfill: last 180 days.
2. Week start: Monday ISO week.
3. Export v1: CSV only.
4. Auto-sync default: off initially, configurable later.
5. Midweek goal edit default: apply next Monday, with optional apply now behavior later.
6. Access model: Tailscale-only first, optional basic auth if exposed beyond private network or if the app is shared beyond one trusted user.
7. Design mode: dark-first, desktop-first, Garmin-inspired tactical dashboard, responsive enough for tablet/mobile but not optimized mobile-first.
8. Working app name: `EnduraSync`.
9. Initial training targets from `../../triathlon_volume_guide_ty_stevens.docx`: Zone 2 starts at 150 minutes/week, increases by 15 to 30 minutes/week during build weeks, and deloads by 20% to 30% every 4th week.
10. Initial session structure: 3 cardio sessions/week, 2 strength sessions/week, 1 flexible easy/mobility session/week, and 1 rest day/week.
11. Initial AI provider preference: local OpenClaw if reachable on the existing Tailscale host `100.69.241.78`; ChatGPT/OpenAI-compatible provider as fallback.

Acceptance criteria:

- Defaults are recorded in `docs/adr/0001-product-defaults.md`.
- Any unresolved decision is explicitly listed under `Open Questions`.
- Later phases can proceed without blocking on product ambiguity.
- The ADR states that AI is expected to recommend weekly goals later, but deterministic defaults keep the app useful before AI is connected.

## P0-B3: Define Fitness Domain Rules Draft

Implementation status: **Implemented.** `docs/domain/classification-rules.md` defines cardio, strength, other, and unknown buckets.

Steps:

1. Create `docs/domain/classification-rules.md`.
2. Draft initial classification buckets: cardio, strength, other, unknown.
3. List obvious cardio sports such as running, cycling, rowing, swimming, hiking, walking, elliptical, stair climber.
4. List obvious strength sports such as weightlifting, functional fitness, strength trainer, resistance training, pilates if desired.
5. Mark ambiguous sports as `unknown` until reviewed.
6. Define that manual annotations may override classification for display/reporting where allowed.

Acceptance criteria:

- Classification rules exist before implementation.
- Unknown/ambiguous values are expected, not treated as bugs.
- Rules are simple enough to unit test later.

---

# P1: Repository Foundation and Local Development Shell

Implementation status: **Implemented on 2026-04-14.** Root structure, env template, README, docs folders, frontend/backend folders, and Makefile command contract exist.

## Goal

Create the monorepo structure, tooling, and basic commands so future phases have a stable place to land.

## Dependencies

- `P0` preferred but not strictly required.

## Outputs

- Root project files.
- `backend/` folder.
- `frontend/` folder.
- `docs/` folder.
- Local env templates.
- Make/npm/task commands for common workflows.

## P1-B1: Initialize Root Project Structure

Implementation status: **Implemented.** `backend/`, `frontend/`, `docs/`, `scripts/`, `deploy/`, `.gitignore`, `.env.example`, `README.md`, `Makefile`, and `docs/README.md` exist.

Steps:

1. Create `backend/`, `frontend/`, `docs/`, `scripts/`, and `deploy/` directories.
2. Create root `.gitignore`.
3. Create root `.env.example`.
4. Create root `README.md`.
5. Create root `Makefile` or package scripts for common commands.
6. Add `docs/README.md` explaining where architecture, ADRs, and runbooks live.

Suggested root structure:

```text
.
├─ backend/
├─ frontend/
├─ deploy/
├─ docs/
│  ├─ adr/
│  ├─ architecture/
│  ├─ domain/
│  └─ runbooks/
├─ scripts/
├─ BUILD_PLAN.md
├─ README.md
├─ .env.example
└─ .gitignore
```

Acceptance criteria:

- Folder structure exists.
- Root README explains local dev intent.
- `.env.example` lists required env vars without real secrets.

## P1-B2: Define Environment Variables

Implementation status: **Implemented.** `.env.example` includes app, database, WHOOP, CORS, auto-sync, and disabled-by-default AI variables without real secrets.

Include at least:

```bash
APP_ENV=development
APP_BASE_URL=http://localhost:8000
FRONTEND_DEV_URL=http://localhost:5173
DATABASE_URL=sqlite:///./data/whoop_dashboard.db
APP_ENCRYPTION_KEY=replace-me
WHOOP_CLIENT_ID=replace-me
WHOOP_CLIENT_SECRET=replace-me
WHOOP_REDIRECT_URI=http://localhost:8000/api/v1/integrations/whoop/callback
CORS_ORIGINS=http://localhost:5173
AUTO_SYNC_ENABLED=false
AUTO_SYNC_FREQUENCY=daily
```

Acceptance criteria:

- `.env.example` contains all required variables.
- No real credentials are present.
- README explains copying `.env.example` to `.env.local` or equivalent.

## P1-B3: Add Developer Command Contract

Implementation status: **Implemented.** Root `Makefile` defines `backend-dev`, `frontend-dev`, `test`, `lint`, `format`, `migrate`, `seed`, and `build`.

Define commands that later phases must keep working:

```bash
make backend-dev
make frontend-dev
make test
make lint
make format
make migrate
make seed
make build
```

If `make` is not desired, use root npm scripts or `just` instead.

Acceptance criteria:

- The command contract is documented even if some commands are placeholders at first.
- Future phases know which commands to implement or preserve.

## P1-B4: Add Baseline Documentation

Implementation status: **Implemented.** `docs/architecture/overview.md`, `docs/runbooks/local-development.md`, and `docs/runbooks/environment.md` exist.

Create:

- `docs/architecture/overview.md`
- `docs/runbooks/local-development.md`
- `docs/runbooks/environment.md`

Acceptance criteria:

- Local setup instructions exist.
- Architecture overview states modular monolith, React/Vite, FastAPI, SQLite, and private deployment.

---

# P2: Backend Foundation, Config, Database, and Migrations

Implementation status: **Implemented on 2026-04-14.** FastAPI app, settings, logging, database session, WAL setup, Alembic baseline, migrations, and backend tests exist.

## Goal

Create a working FastAPI backend with typed settings, logging, SQLite, SQLAlchemy, Alembic, health checks, and test scaffolding.

## Dependencies

- `P1`

## Outputs

- Runnable backend app.
- Health endpoint.
- Config module.
- Database session module.
- Alembic migration baseline.
- Pytest setup.

## P2-B1: Scaffold Python Project

Implementation status: **Implemented.** Backend app is under `backend/app`, with `main.py`, API routes, core modules, DB modules, Alembic config, and tests.

Recommended files:

```text
backend/
├─ app/
│  ├─ api/
│  │  ├─ deps.py
│  │  └─ routes/
│  │     └─ health.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ logging.py
│  │  ├─ security.py
│  │  └─ time.py
│  ├─ db/
│  │  ├─ base.py
│  │  └─ session.py
│  └─ main.py
├─ tests/
│  └─ test_health.py
├─ alembic.ini
└─ pyproject.toml
```

Acceptance criteria:

- `uvicorn app.main:app --reload` can start the app from `backend/`.
- `GET /health` returns app status.
- `GET /api/v1/health` returns app status.

## P2-B2: Add Typed Settings

Implementation status: **Implemented.** Pydantic settings load env files/variables, allow local placeholders, validate production secrets, and include WHOOP/AI/sync config.

Steps:

1. Add Pydantic settings model.
2. Load env vars for app env, base URL, database URL, CORS origins, WHOOP credentials, encryption key, and sync preferences.
3. Validate required secrets in production.
4. Allow relaxed placeholders in development.

Acceptance criteria:

- Missing production secrets fail fast.
- Development can boot with placeholder WHOOP credentials if OAuth is not used yet.
- Tests can override settings safely.

## P2-B3: Add Logging Foundation

Implementation status: **Implemented.** Startup logging records app name, environment, and version without secrets.

Steps:

1. Configure structured-ish logs with timestamp, level, module, and message.
2. Avoid logging secrets.
3. Add request logging middleware only if it stays low-noise.
4. Add sync-specific logging fields later.

Acceptance criteria:

- Backend startup logs environment and version metadata.
- Health checks do not spam logs excessively.

## P2-B4: Add Database Session and SQLite WAL

Implementation status: **Implemented.** SQLAlchemy engine/session setup creates the SQLite parent directory, enables WAL/foreign keys, supports in-memory tests, and exposes health connectivity checks.

Steps:

1. Configure SQLAlchemy engine.
2. Add session dependency.
3. Ensure SQLite parent directory exists.
4. Enable WAL mode for SQLite.
5. Add simple database connectivity check.

Acceptance criteria:

- Backend can connect to SQLite.
- WAL mode is enabled or attempted safely.
- Database path is configurable.

## P2-B5: Add Alembic Baseline

Implementation status: **Implemented.** Alembic is wired to SQLAlchemy metadata with baseline migration `0001_baseline.py`; `make migrate` runs cleanly.

Steps:

1. Initialize Alembic.
2. Wire SQLAlchemy metadata.
3. Create empty baseline migration.
4. Add `make migrate` command.
5. Document migration workflow.

Acceptance criteria:

- Migration command runs cleanly.
- Empty database can be created from migrations.

## P2-B6: Add Backend Test Harness

Implementation status: **Implemented.** Pytest, FastAPI test client, isolated in-memory SQLite fixture, health tests, settings/profile tests, OAuth tests, and repository tests exist.

Steps:

1. Add pytest.
2. Add HTTPX test client.
3. Add isolated SQLite test database fixture.
4. Add health endpoint tests.
5. Add settings override fixture.

Acceptance criteria:

- `pytest` passes.
- Tests do not touch production/local dev database.

---

# P3: Frontend Foundation and Visual Design System

Implementation status: **Implemented on 2026-04-14 as foundation.** React/Vite app, routes, app shell, dark tactical styling, UI primitives, TanStack Query, and API helper exist.

## Goal

Create a React/Vite frontend with routing, query client, app shell, design tokens, dark-first styling, and placeholder pages.

## Dependencies

- `P1`
- `P2` helpful for API proxy/health integration

## Outputs

- Runnable frontend.
- App shell.
- Navigation.
- Placeholder routes.
- Design token foundation.
- Query client foundation.

## P3-B1: Scaffold React App

Implementation status: **Implemented.** `frontend/` contains Vite, TypeScript, Tailwind, app/router/provider files, routes, components, styles, and library helpers.

Recommended files:

```text
frontend/
├─ src/
│  ├─ app/
│  │  ├─ App.tsx
│  │  ├─ providers.tsx
│  │  └─ router.tsx
│  ├─ components/
│  │  ├─ layout/
│  │  └─ ui/
│  ├─ features/
│  │  ├─ dashboard/
│  │  ├─ goals/
│  │  ├─ reports/
│  │  ├─ settings/
│  │  └─ sync/
│  ├─ lib/
│  │  ├─ api.ts
│  │  ├─ dates.ts
│  │  └─ format.ts
│  ├─ routes/
│  ├─ styles/
│  │  └─ globals.css
│  └─ main.tsx
├─ index.html
├─ package.json
├─ tsconfig.json
└─ vite.config.ts
```

Acceptance criteria:

- `npm run dev` starts frontend.
- App renders without backend data.
- TypeScript compiles.

## P3-B2: Add Routing

Implementation status: **Implemented.** `/` redirects to `/dashboard`; dashboard, goals, recovery-strain, six-month report, settings, and not-found routes render.

Routes:

- `/` redirects to `/dashboard`.
- `/dashboard`
- `/goals`
- `/recovery-strain`
- `/reports/six-month`
- `/settings`

Acceptance criteria:

- All routes render placeholder pages.
- Navigation highlights active route.
- Unknown routes render a friendly not-found page.

## P3-B3: Add Visual Direction

Implementation status: **Implemented as foundation.** CSS variables, dark tactical surfaces, bright accent colors, and central HR-zone colors exist.

Design principles:

- Dark-first.
- Premium private cockpit, not spreadsheet UI.
- Strong HR-zone color identity.
- Calm surfaces with bright, intentional accents.
- Desktop-first spacing.
- Clear visual hierarchy.

Suggested design tokens:

```text
background: near-black blue/graphite
surface: layered charcoal
surface-raised: slightly lighter graphite
text-primary: warm white
text-muted: blue-gray
accent: electric cyan or lime, not generic purple
zone1: cool cyan
zone2: green
zone3: yellow
zone4: orange
zone5: red/coral
recovery: green/teal spectrum
strain: amber/red spectrum
```

Acceptance criteria:

- CSS variables exist for theme tokens.
- HR-zone color map exists in one frontend module.
- Placeholder pages already feel like the intended product, not default boilerplate.

## P3-B4: Add UI Primitives

Implementation status: **Implemented.** `Card`, `Button`, `ProgressBar`, `StatBlock`, `PageHeader`, `EmptyState`, `LoadingState`, `ErrorState`, `Badge`, and `SectionShell` exist.

Create initial primitives:

- `Card`
- `Button`
- `ProgressBar`
- `StatBlock`
- `PageHeader`
- `EmptyState`
- `LoadingState`
- `ErrorState`
- `Badge`
- `SectionShell`

Acceptance criteria:

- Primitives are reusable and typed.
- Pages use primitives rather than ad hoc HTML everywhere.
- Components support dark theme well.

## P3-B5: Add TanStack Query and API Client Shell

Implementation status: **Implemented.** Query client provider, JSON fetch helper, typed API shapes, backend health query, and Vite dev proxy exist.

Steps:

1. Add query client provider.
2. Add API base URL handling.
3. Add JSON fetch helper with typed error shape.
4. Add placeholder health query.
5. Add dev proxy if helpful.

Acceptance criteria:

- Frontend can call backend health endpoint.
- API errors render a sane message.
- Query client is available to all pages.

---

# P4: WHOOP OAuth Connection and Secure Token Lifecycle

Implementation status: **Mostly implemented on 2026-04-14.** OAuth routes, state persistence/validation, token exchange boundary, encrypted token storage, connection table, status, disconnect, and Settings UI states exist. Proactive refresh/retry remains.

## Goal

Implement server-side WHOOP OAuth authorization code flow, token persistence, refresh, reconnect, and disconnect.

## Dependencies

- `P2`
- Basic docs from `P0`

## Outputs

- WHOOP auth routes.
- Secure token storage.
- Connection status endpoint.
- Token refresh service.
- Tests for token lifecycle.

## P4-B1: Create WHOOP Integration Module

Implementation status: **Implemented.** `backend/app/services/whoop/` contains `auth_service.py`, `client.py`, `models.py`, `oauth.py`, and `token_store.py`; all planned routes exist.

Recommended backend structure:

```text
backend/app/services/whoop/
├─ auth_service.py
├─ client.py
├─ models.py
├─ oauth.py
└─ token_store.py
```

Routes:

- `GET /api/v1/integrations/whoop/connect`
- `GET /api/v1/integrations/whoop/callback`
- `GET /api/v1/integrations/whoop/status`
- `POST /api/v1/integrations/whoop/disconnect`

Acceptance criteria:

- Routes exist.
- Connect route redirects to WHOOP authorization URL.
- Callback route validates state and exchanges code for tokens.

## P4-B2: Add Connection Table

Implementation status: **Implemented.** `WhoopConnectionModel` and migration `0002_p4_persistence_foundation.py` create `whoop_connection` with encrypted token fields and `whoop_user_id` uniqueness.

Model: `whoop_connection`

Fields:

- `id`
- `whoop_user_id`
- `status`
- `access_token_encrypted`
- `refresh_token_encrypted`
- `token_expires_at_utc`
- `granted_scopes`
- `connected_at_utc`
- `last_token_refresh_at_utc`
- `created_at_utc`
- `updated_at_utc`

Acceptance criteria:

- Migration creates the table.
- Unique constraint exists for `whoop_user_id` if available.
- Status values are constrained or validated.

## P4-B3: Add Token Encryption

Implementation status: **Implemented.** `core/security.py` provides encryption/decryption helpers using `APP_ENCRYPTION_KEY`; token store encrypts before write and decrypts only inside service code; tests prove plaintext is not persisted.

Steps:

1. Implement encryption helpers in `core/security.py`.
2. Use app-level encryption key from env.
3. Encrypt access and refresh tokens before database write.
4. Decrypt only inside token service.
5. Never return token values in API responses.

Acceptance criteria:

- Database never stores plaintext WHOOP tokens.
- Tests prove round-trip encryption/decryption works.
- Logs do not include token values.

## P4-B4: Add Token Refresh Logic

Implementation status: **Implemented via P6-S4 on 2026-04-14.** The token store refreshes expiring tokens before provider calls, the authenticated provider client retries once after a 401, `last_token_refresh_at_utc` is updated after refresh, and persistent refresh failure marks the connection `error`.

Rules:

- Refresh proactively if expiry is near.
- Retry once after a 401 by refreshing token.
- Update `last_token_refresh_at_utc`.
- Mark connection as `error` if refresh fails persistently.

Acceptance criteria:

- Refresh service can be called by sync engine.
- Expired tokens are refreshed before API calls.
- Failed refresh surfaces in status endpoint.

## P4-B5: Add Connection Status UI Placeholder

Implementation status: **Implemented and lightly polished.** Settings page shows WHOOP status, connect/reconnect, disconnect for connected/expired states, scopes, connected timestamp, and token expiry when available.

Frontend settings page should display:

- Connected/disconnected/error state.
- Connect button.
- Disconnect button.
- Last connected or refresh timestamp if available.
- Friendly token error state.

Acceptance criteria:

- User can initiate OAuth from settings.
- UI does not expose secrets.
- Disconnected state is understandable.

---

# P5: Canonical Data Schema and Persistence Repositories

Implementation status: **Implemented on 2026-04-14.** Canonical fact models, overlay/audit models, migration `0003_p5_canonical_schema.py`, repository layer, and repository tests exist.

## Goal

Create the canonical local data model for workouts, sleeps, recoveries, goals, sync state, sync runs, settings, and annotations.

## Dependencies

- `P2`
- `P4` for connection table

## Outputs

- ORM models.
- Migrations.
- Repository classes.
- Indexes and constraints.
- Data integrity tests.

## P5-B1: Create Imported Fact Models

Implementation status: **Implemented.** `WorkoutModel`, `SleepModel`, and `RecoveryModel` exist in `backend/app/models/facts.py`.

Tables:

- `workouts`
- `sleeps`
- `recoveries`

Important rules:

- Use external IDs for uniqueness.
- Store provider timestamps.
- Store local date buckets.
- Store raw payload JSON for latest version.
- Store payload hash.
- Store source revision.
- Store zone durations as integer seconds.

Acceptance criteria:

- Tables exist.
- Unique indexes exist.
- Date bucket indexes exist.
- Zone columns are wide typed integer columns, not JSON-only.

## P5-B2: Create Workouts Schema

Implementation status: **Implemented.** Migration and ORM include the planned workout fields, uniqueness, date indexes, zone columns, classification check, payload hash, raw JSON, and source revision.

Fields:

- `id`
- `external_id`
- `external_v1_id`
- `whoop_user_id`
- `external_created_at_utc`
- `external_updated_at_utc`
- `start_time_utc`
- `end_time_utc`
- `timezone_offset_text`
- `local_start_date`
- `iso_week_start_date`
- `local_month_start_date`
- `sport_name`
- `score_state`
- `classification`
- `duration_seconds`
- `strain`
- `average_hr`
- `max_hr`
- `percent_recorded`
- `zone0_seconds`
- `zone1_seconds`
- `zone2_seconds`
- `zone3_seconds`
- `zone4_seconds`
- `zone5_seconds`
- `raw_payload_json`
- `payload_hash`
- `source_revision`
- `imported_at_utc`

Acceptance criteria:

- Migration includes all fields.
- Duration values are seconds.
- Classification is validated.

## P5-B3: Create Sleeps Schema

Implementation status: **Implemented.** Migration and ORM include the planned sleep fields, uniqueness, nap flag, date indexes, payload hash, raw JSON, and source revision.

Fields:

- `id`
- `external_id`
- `external_v1_id`
- `cycle_id`
- `whoop_user_id`
- `external_created_at_utc`
- `external_updated_at_utc`
- `start_time_utc`
- `end_time_utc`
- `timezone_offset_text`
- `local_start_date`
- `iso_week_start_date`
- `local_month_start_date`
- `nap`
- `score_state`
- `sleep_duration_seconds`
- `sleep_performance`
- `sleep_efficiency`
- `raw_payload_json`
- `payload_hash`
- `source_revision`
- `imported_at_utc`

Acceptance criteria:

- Sleep records can be queried by week and month.
- Naps are represented explicitly.

## P5-B4: Create Recoveries Schema

Implementation status: **Implemented.** Migration and ORM include the planned recovery fields, `cycle_id` uniqueness, date indexes, payload hash, raw JSON, and source revision.

Fields:

- `id`
- `cycle_id`
- `sleep_external_id`
- `whoop_user_id`
- `external_created_at_utc`
- `external_updated_at_utc`
- `local_date`
- `iso_week_start_date`
- `local_month_start_date`
- `score_state`
- `recovery_score`
- `hrv_ms`
- `resting_hr`
- `respiratory_rate`
- `skin_temp_celsius`
- `spo2_percent`
- `raw_payload_json`
- `payload_hash`
- `source_revision`
- `imported_at_utc`

Acceptance criteria:

- Recovery records can be queried by local date, week, and month.
- `cycle_id` uniqueness is enforced.

## P5-B5: Create Overlay and App Tables

Implementation status: **Implemented.** `workout_annotations`, `goal_profiles`, `sync_state`, `sync_runs`, and `app_settings` tables exist. `athlete_profile` also exists from the early settings/profile work.

Tables:

- `workout_annotations`
- `goal_profiles`
- `sync_state`
- `sync_runs`
- `app_settings`

Acceptance criteria:

- Manual annotations are separate from imported workouts.
- Goal profiles have effective dates.
- Sync runs are append-only.
- Sync state stores compact cursor/watermark per resource.
- Settings table supports auto-sync preferences.

## P5-B6: Create Repository Layer

Implementation status: **Implemented.** Repositories exist for workouts, sleeps, recoveries, goals, sync, settings/profile exports, and annotations. Tests cover insert/update/unchanged upserts, uniqueness, date lookups, annotations, goals, and sync state/runs.

Repositories:

- `workouts.py`
- `sleeps.py`
- `recoveries.py`
- `goals.py`
- `sync.py`
- `settings.py`
- `annotations.py`

Acceptance criteria:

- Routes and services do not write raw SQL directly except in deliberate aggregate queries.
- Upsert methods exist for imported facts.
- Repository tests cover insert, update, duplicate, and date-range lookup behavior.

---

# P6: WHOOP Client, Transformers, and Sync Engine

Implementation status: **Implemented for local gates.** `P6-S1` through `P6-S6` are implemented, including date bucket helpers, workout classification, provider models/fixtures, payload hashing/transformers, token refresh/authenticated provider client, sync orchestrator, sync status/run APIs, and scheduled job command. Real WHOOP smoke testing remains a manual launch gate.

## Goal

Fetch WHOOP workouts, sleeps, and recoveries; validate provider payloads; transform into canonical records; upsert safely; and record sync audit state.

## Dependencies

- `P4`
- `P5`

## Outputs

- WHOOP HTTP client.
- Pydantic provider models.
- Transformers.
- Sync orchestrator.
- Manual sync endpoint.
- Sync command for cron/systemd.
- Sync status endpoint.

## Recommended P6 Execution Slices

Implementation note: **Do not implement all of P6 in one pass.** Keep each slice independently testable and stop after each slice with `make test`, `make lint`, and `make build`.

1. `P6-S1`: Date bucket helpers and workout classification.
   - Implementation status: **Implemented on 2026-04-14.**
   - Add backend helpers for local date, ISO week start, and month start.
   - Add deterministic sport classification from `docs/domain/classification-rules.md`.
   - Tests should cover Sunday/Monday boundaries, month boundaries, workouts crossing midnight, known cardio, known strength, and unknown sports.

2. `P6-S2`: WHOOP provider Pydantic models and fixture payloads.
   - Implementation status: **Implemented on 2026-04-14.**
   - Add provider response models for workouts, sleeps, recoveries, pagination, and score/state objects.
   - Add small fixture payloads for scored and pending records.
   - Tests should validate optional fields and `PENDING_SCORE`-style states without crashes.

3. `P6-S3`: Payload hashing and transformers.
   - Implementation status: **Implemented on 2026-04-14.**
   - Transform provider models into dictionaries accepted by the P5 repositories.
   - Normalize all durations to seconds.
   - Preserve latest raw payload JSON server-side.
   - Tests should cover negative duration rejection, malformed-record skip behavior, missing optional metrics, zone extraction, and payload hash stability.

4. `P6-S4`: Token refresh and authenticated WHOOP client.
   - Implementation status: **Implemented on 2026-04-14.**
   - Finish the P4 refresh gap here.
   - Refresh proactively when expiry is near.
   - Retry one authenticated request after a 401.
   - Retry 429/5xx with bounded backoff.
   - Tests should use mocked HTTP only; do not require real WHOOP credentials.

5. `P6-S5`: Sync orchestrator with mocked WHOOP client.
   - Implementation status: **Implemented on 2026-04-14.**
   - Wire fetch, validate, transform, repository upsert, sync run counts, and sync state updates.
   - Prove repeated windows are idempotent.
   - Failed sync must not advance sync state.

6. `P6-S6`: Manual sync API and job command.
   - Implementation status: **Implemented on 2026-04-14.**
   - Replace sync placeholder routes with real orchestration.
   - Add `python -m app.jobs.run_sync --trigger scheduled`.
   - Keep concurrency protection simple for v1: reject or no-op when a run is already active.

7. `P6-S7`: Real WHOOP smoke path.
   - Only after mocked sync is green, test one real credential-backed connection and manual sync.
   - Do not commit credentials, token values, or raw response dumps from a real account.

## P6-B1: Implement WHOOP HTTP Client

Implementation status: **Implemented via P6-S4 on 2026-04-14 for authenticated collection fetching.** `WhoopProviderClient` attaches bearer tokens, refreshes before expiry, follows collection pagination, retries one 401 after refresh, and retries 429/5xx with bounded backoff using mocked HTTP tests.

Responsibilities:

- Add authorization headers.
- Refresh token when needed.
- Handle pagination.
- Handle date windows.
- Retry transient errors.
- Respect rate limits.
- Normalize error responses.

Acceptance criteria:

- Client can make authenticated requests.
- 401 triggers one token refresh and retry.
- 429 and 5xx errors retry with backoff.
- Persistent errors are surfaced, not swallowed.

## P6-B2: Implement Provider Models

Implementation status: **Implemented via P6-S2 on 2026-04-14.** `backend/app/services/whoop/provider_models.py` defines workout, sleep, recovery, nested score, zone duration, and collection response models. Synthetic scored/pending fixtures and validation tests exist under `backend/tests/fixtures/whoop/` and `backend/tests/test_whoop_provider_models.py`.

Create typed models for:

- Workout collection response.
- Workout item.
- Sleep collection response.
- Sleep item.
- Recovery collection response.
- Recovery item.
- Pagination metadata.
- Score/state objects.

Acceptance criteria:

- Provider payloads are validated before transformation.
- Optional fields are handled as nullable, not crashes.
- `PENDING_SCORE` and similar states can persist.

## P6-B3: Implement Date Bucket Helpers

Helpers must derive:

- `local_start_date`
- `local_date`
- `iso_week_start_date`
- `local_month_start_date`

Rules:

- ISO week starts Monday.
- Use provider/local timezone information when available.
- Keep UTC timestamps for canonical event times.
- Store date buckets during import for consistent downstream calculations.

Acceptance criteria:

- Unit tests cover Sunday/Monday boundaries.
- Unit tests cover workouts crossing midnight.
- Unit tests cover month boundary behavior.

## P6-B4: Implement Workout Classification

Steps:

1. Implement deterministic sport-name mapping.
2. Return `cardio`, `strength`, `other`, or `unknown`.
3. Keep mapping in one backend module.
4. Add tests from `docs/domain/classification-rules.md`.

Acceptance criteria:

- Known cardio sports classify as cardio.
- Known strength sports classify as strength.
- Ambiguous or missing sports classify as unknown.
- Classification can be changed later without touching sync core.

## P6-B5: Implement Transformers

Implementation status: **Implemented via P6-S3 on 2026-04-14.** `backend/app/services/whoop/transformers.py` computes stable SHA-256 payload hashes, converts WHOOP provider models into canonical fact dictionaries, normalizes durations to seconds, derives date buckets, classifies workouts, preserves raw payload JSON, and is covered by fixture-driven transformer and repository smoke tests.

Transform WHOOP records into canonical internal shapes:

- Workout transformer.
- Sleep transformer.
- Recovery transformer.

Each transformer should:

- Validate timestamp order.
- Normalize durations to seconds.
- Extract zone seconds.
- Calculate payload hash.
- Attach source revision behavior inputs.
- Preserve raw payload JSON.

Acceptance criteria:

- Malformed single payload can be logged and skipped.
- Negative durations are rejected.
- Missing optional metrics become null.
- Raw payloads are available for debugging.

## P6-B6: Implement Upsert and Source Revision Rules

Implementation status: **Implemented at repository layer in P5.** `WorkoutRepository`, `SleepRepository`, and `RecoveryRepository` insert new records, return unchanged for repeated payloads, update on newer provider timestamps or changed payload hashes, increment `source_revision`, and preserve manual annotations.

Rules:

- Insert if external ID is new.
- Update if provider `updated_at` is newer.
- Update if payload hash differs even when `updated_at` is unchanged.
- Increment `source_revision` on update.
- Do not touch manual annotations during provider updates.
- Do not delete local rows just because they are absent from a later fetch.

Acceptance criteria:

- Repeated sync of same payload results in unchanged count.
- Updated payload increments revision once.
- Manual annotations survive workout update.

## P6-B7: Implement Sync Orchestrator

Implementation status: **Implemented via P6-S5 on 2026-04-14.** `SyncOrchestrator` creates per-resource sync runs, computes backfill/incremental windows, fetches mocked provider pages, transforms raw/provider records, upserts through canonical repositories, records counts, marks success/partial/failed, and advances sync state only after successful runs.

Sync modes:

- `initial_backfill`
- `manual`
- `scheduled`

Resource types:

- `workouts`
- `sleeps`
- `recoveries`

Process:

1. Create sync run row.
2. Compute date/update window.
3. Fetch pages.
4. Validate records.
5. Transform records.
6. Upsert records.
7. Count inserted, updated, unchanged, failed.
8. Commit safely.
9. Advance sync state only after success.
10. Mark sync run success, partial, or failed.

Acceptance criteria:

- Sync runs are visible in database.
- Failed sync does not advance watermark incorrectly.
- Initial backfill defaults to 180 days.
- Incremental sync uses overlap.

## P6-B8: Add Sync API and Job Command

Implementation status: **Implemented via P6-S6 on 2026-04-14.** Sync status/run API routes now report/run the backend orchestrator, reject concurrent runs, return run counts/outcomes, and `python -m app.jobs.run_sync --trigger scheduled` exists for cron/systemd wiring.

Routes:

- `GET /api/v1/sync/status`
- `POST /api/v1/sync/run`

Command:

- `python -m app.jobs.run_sync --trigger scheduled`
- Optional date-window arguments for debugging.

Acceptance criteria:

- Manual refresh endpoint starts or runs sync safely.
- Sync status endpoint returns running, success, partial, failed, last success, and counts.
- Job command can be called by cron/systemd later.

---

# P7: Goal Profiles, Settings, and Effective-Date Logic

Implementation status: **Implemented.** App settings, athlete profile APIs, goal profile effective-date service behavior, goal APIs, overlap handling, and idempotent seed defaults exist.

## Goal

Allow the user to define weekly training targets without changing code while preserving historical truth.

## Dependencies

- `P5`

## Outputs

- Goal profile services.
- Settings services.
- Athlete profile service.
- Goal APIs.
- Settings APIs.
- Athlete profile APIs.
- Tests for effective-date resolution.

## P7-B1: Implement Goal Profile Model Behavior

Implementation status: **Implemented via P7-S1 on 2026-04-14.** `goal_profiles` table and repository basics exist; `GoalProfileService` requires Monday effective dates, rejects invalid ranges/overlaps, closes the previous open-ended profile safely, preserves historical rows, and seeds defaults idempotently.

Fields:

- `effective_from_date`
- `effective_to_date`
- `zone1_target_minutes`
- `zone2_target_minutes`
- `zone3_target_minutes`
- `zone4_target_minutes`
- `zone5_target_minutes`
- `cardio_sessions_target`
- `strength_sessions_target`
- `created_reason`
- `created_at_utc`

Rules:

- Goals are inserted as new profiles.
- Existing historical profiles are not overwritten.
- Profile resolution uses requested week start date.
- Overlapping active profiles are rejected or automatically closed safely.

Acceptance criteria:

- Active profile can be resolved for any week.
- Historical week uses historical goal profile.
- Overlap tests pass.

## P7-B2: Implement Goal APIs

Implementation status: **Implemented via P7-S1 on 2026-04-14.** `/api/v1/goals/active`, `/history`, `/for-week`, and `POST /api/v1/goals/` exist with validation and versioned goal profile responses.

Routes:

- `GET /api/v1/goals/active`
- `GET /api/v1/goals/history`
- `POST /api/v1/goals`
- `GET /api/v1/goals/for-week?week_start_date=YYYY-MM-DD`

Acceptance criteria:

- Invalid negative targets are rejected.
- Goal changes create new versioned rows.
- Response clearly states effective dates.

## P7-B3: Implement App Settings

Implementation status: **Implemented.** `GET /api/v1/settings` and `PUT /api/v1/settings` are database-backed, validate the current schema, and return defaults if no row exists.

Settings:

- Auto-sync enabled.
- Auto-sync frequency: daily or twice daily.
- Preferred export format defaults.
- Preferred units if needed.
- Optional app-level display preferences.

Routes:

- `GET /api/v1/settings`
- `PUT /api/v1/settings`

Acceptance criteria:

- Settings can be read and updated.
- Invalid frequency is rejected.
- Settings have sane defaults if no row exists.

## P7-B4: Implement Athlete Profile

Implementation status: **Implemented.** `GET /api/v1/athlete-profile` and `PUT /api/v1/athlete-profile` are database-backed, tolerate incomplete values, validate age/height/weight, and expose `ai_context_allowed` based on AI configuration.

Purpose:

- Store basic user context that improves training interpretation and future AI suggestions.
- Keep profile data separate from WHOOP imported facts.
- Allow the dashboard to work even if profile fields are incomplete.

Fields:

- `display_name`
- `gender`
- `date_of_birth` or `age_years`
- `height_cm`
- `weight_kg`
- `training_focus`
- `experience_level`
- `notes_for_ai`
- `updated_at_utc`

Rules:

- Profile data is editable from settings.
- Age should be derived from date of birth if date of birth is stored.
- If the user prefers not to store date of birth, store `age_years` instead.
- Height and weight are optional but validated when present.
- Profile data can be included in AI context only if AI is enabled.
- Profile data should not be included in CSV exports unless explicitly requested later.

Routes:

- `GET /api/v1/athlete-profile`
- `PUT /api/v1/athlete-profile`

Acceptance criteria:

- The user can enter gender, age or date of birth, height, and weight.
- Invalid values are rejected with clear validation errors.
- Missing profile values do not break metrics or reports.
- AI context builder includes profile context when present and excludes it when AI is disabled.

## P7-B5: Seed Initial Goal Profile

Implementation status: **Implemented.** `make seed` runs an idempotent default goal profile seed command and reports the effective defaults.

Steps:

1. Add seed command or first-run setup behavior.
2. Insert default goal profile if none exists.
3. Make defaults obviously editable.
4. Document where defaults come from.

Acceptance criteria:

- Dashboard metrics can compute even before user edits goals.
- Seed command is safe to rerun.

---

# P8: Metrics Engine and Report Dataset Builder

## Goal

Build the deterministic backend metrics layer that powers dashboard, trends, reports, exports, and future AI summaries.

## Dependencies

- `P5`
- `P6`
- `P7`

## Outputs

- Current week summary service.
- Monthly summary service.
- Rolling trends service.
- 6-month dataset builder.
- Golden fixture tests.

## P8-B1: Create Metrics Module

Implementation status: **Implemented for Version 1 local gates on 2026-04-17.** `backend/app/services/metrics/` contains current-week, recovery/strain trend, rolling comparison, consistency, and six-month report dataset services with typed DTOs and tests.

Recommended structure:

```text
backend/app/services/metrics/
├─ current_week.py
├─ monthly.py
├─ rolling.py
├─ report_dataset.py
├─ consistency.py
└─ types.py
```

Rules:

- Metrics services read facts and goals.
- Metrics services do not mutate canonical data.
- Formulas live in one place.
- Response DTOs include raw values and display-friendly derived values.

Acceptance criteria:

- No metric formula is duplicated in API routes or frontend.
- Unit tests can call metrics services without FastAPI request objects.

## P8-B2: Implement Current Week Summary

Implementation status: **Implemented via P8-S1 on 2026-04-14.** Current-week metrics read canonical workouts/recoveries, active goal profiles, and sync state; return zone progress, session progress, total training seconds, average recovery, and average strain; and cover empty, partial, over-target, missing-goal, zero-target, historical-goal, and invalid-week cases with tests.

Inputs:

- Week start date.
- Workouts in ISO week.
- Recoveries in ISO week.
- Active goal profile for week.

Outputs:

- Week start and end.
- Last successful sync timestamp.
- Zone progress for zones 1 through 5.
- Actual seconds.
- Target minutes.
- Percent complete.
- Remaining minutes.
- Exceeded flag.
- Cardio sessions completed and target.
- Strength sessions completed and target.
- Total training seconds.
- Average recovery score.
- Average daily strain.

Acceptance criteria:

- Zone targets of zero do not divide by zero.
- Remaining minutes never go below zero.
- Exceeded flag works.
- Tests cover empty week, partial week, and over-target week.

## P8-B3: Implement Monthly Summaries

Implementation status: **Implemented on 2026-04-17.** Six-month report metrics aggregate monthly training volume, zone minutes, classification counts, recovery, and strain.

Aggregate by `local_month_start_date`:

- Total training time.
- Zone seconds/minutes by month.
- Cardio sessions.
- Strength sessions.
- Other/unknown sessions.
- Average strain.
- Average recovery.
- Average HRV.
- Average resting HR.

Acceptance criteria:

- Monthly values aggregate from raw facts, not averaged weekly percentages.
- Empty months can be represented for chart continuity.

## P8-B4: Implement Rolling Recovery and Strain Trends

Implementation status: **Implemented on 2026-04-17.** Recovery/strain metrics produce weekly series, four-week comparison cards, recovery-per-strain context, and deterministic interpretation text.

Recommended metrics:

- Weekly average recovery score.
- Weekly average daily strain.
- 4-week rolling recovery average.
- 4-week rolling strain average.
- 8-week rolling recovery average.
- 8-week rolling strain average.
- Recovery per strain unit.
- Percentage of weeks hitting Zone 2 target.

Acceptance criteria:

- Rolling windows are transparent and testable.
- Insufficient data returns null or clear empty state metadata.
- No pseudo-scientific hidden scores are introduced.

## P8-B5: Implement Consistency Metrics

Implementation status: **Implemented on 2026-04-17.** Six-month report metrics include week coverage for training, sleep, and recovery plus simple summary text.

Potential metrics:

- Training days per week.
- Weeks hitting Zone 2 target.
- Weeks hitting total volume target.
- Weeks meeting cardio target.
- Weeks meeting strength target.
- Percent of weeks meeting critical goals.

Acceptance criteria:

- Each consistency metric has a documented formula.
- Tests use golden fixtures.

## P8-B6: Implement 6-Month Dataset Builder

Implementation status: **Implemented on 2026-04-17.** `SixMonthReportMetricsService` builds the shared dataset used by the report API and CSV export.

Default range:

- Last 26 completed or current ISO weeks.

Dataset includes:

- Date range metadata.
- Monthly summary rows.
- Weekly trend rows.
- Consistency metrics.
- Current goal profile context.
- Athlete profile context for optional AI use, not for normal report display unless requested.
- Export metadata.

Acceptance criteria:

- Report page and CSV export can consume the same object.
- Date range is deterministic.
- Dataset is snapshot tested.

---

# P9: Backend API Contracts and Typed Frontend Client

Implementation status: **Implemented for Version 1 local gates on 2026-04-17.** API groups cover health, WHOOP OAuth/status/disconnect, sync status/run, settings, athlete profile, goals, current-week dashboard metrics, recovery/strain trends, six-month report, and CSV export. Workout annotation APIs remain Version 1.5/P17.

## Goal

Expose cohesive, typed API endpoints for dashboard, goals, sync, settings, reports, and annotations.

## Dependencies

- `P6`
- `P7`
- `P8`

## Outputs

- Route groups.
- Pydantic schemas.
- OpenAPI schema.
- Typed frontend client or manually maintained TypeScript types.

## P9-B1: Create Route Groups

Implementation status: **Implemented for Version 1 local gates on 2026-04-17.** Registered `/api/v1` routes include the core dashboard, goals, sync, settings, athlete profile, WHOOP, recovery/strain, report, and CSV surfaces.

Routes:

- `GET /api/v1/dashboard/current-week`
- `GET /api/v1/dashboard/recent-trends`
- `GET /api/v1/goals/active`
- `GET /api/v1/goals/history`
- `POST /api/v1/goals`
- `GET /api/v1/reports/six-month`
- `GET /api/v1/reports/six-month/export.csv`
- `GET /api/v1/sync/status`
- `POST /api/v1/sync/run`
- `GET /api/v1/settings`
- `PUT /api/v1/settings`
- `GET /api/v1/athlete-profile`
- `PUT /api/v1/athlete-profile`
- `GET /api/v1/integrations/whoop/connect`
- `GET /api/v1/integrations/whoop/callback`
- `GET /api/v1/integrations/whoop/status`
- `POST /api/v1/integrations/whoop/disconnect`
- `PATCH /api/v1/workouts/{id}/annotation`

Acceptance criteria:

- Routes are registered under `/api/v1`.
- Route handlers stay thin.
- Business logic remains in services.

## P9-B2: Define Stable Response Shapes

Implementation status: **Implemented for Version 1 local gates on 2026-04-17.** Stable Pydantic response shapes exist for health, WHOOP status, app settings, athlete profile, sync status/run, goals, current-week dashboard metrics, recovery/strain trends, reports, and CSV export.

Rules:

- Use explicit field names.
- Include units in names or adjacent metadata.
- Return chart-ready series where domain aggregation is non-trivial.
- Include timestamps in ISO 8601 UTC.
- Include enough metadata for empty states.

Acceptance criteria:

- Frontend should not guess units.
- Frontend should not calculate goal percentages itself.
- Frontend should not need raw WHOOP payloads.

## P9-B3: Generate or Maintain TypeScript Types

Implementation status: **Implemented via maintained TypeScript types on 2026-04-17.** Manual API types in `frontend/src/lib/api.ts` cover the Version 1 frontend surfaces; generated OpenAPI client/types remain optional future hardening.

Preferred approach:

1. Generate OpenAPI schema from FastAPI.
2. Generate TypeScript client/types from OpenAPI.
3. Commit generated types if that fits workflow.

Fallback approach:

1. Maintain types manually in `frontend/src/types/api.ts`.
2. Keep names aligned with Pydantic schemas.
3. Add contract tests for key endpoints.

Acceptance criteria:

- Dashboard frontend code uses typed API responses.
- Type drift is caught by build or tests.

---

# P10: Dashboard Home Page and Manual Refresh UX

Implementation status: **Implemented on 2026-04-17.** Dashboard route renders backend current-week metrics, zone progress, session progress, recovery/strain snapshot, sync status, and manual refresh flow.

## Goal

Build the main dashboard screen that answers the core product question in under 10 seconds: what have I done this week, what remains, and how am I trending?

## Dependencies

- `P3`
- `P9`

## Outputs

- Dashboard page.
- Weekly progress cards.
- Zone progress grid.
- Remaining targets card.
- Session progress card.
- Recovery snapshot card.
- Sync status card.
- Manual refresh flow.

## P10-B1: Build Dashboard Layout

Implementation status: **Implemented.** The page has backend-powered current week header, primary progress cards, HR-zone grid, recovery/strain snapshot, and sync status/refresh controls.

Sections, top to bottom:

1. Page header with current week date range and last sync.
2. Primary weekly progress headline.
3. HR-zone progress grid.
4. Remaining targets card.
5. Cardio and strength session progress.
6. Recovery snapshot.
7. Recent trend strip.
8. Sync status and refresh control.

Acceptance criteria:

- Weekly progress is the visual priority.
- The page does not feel cluttered.
- User can understand status quickly.

## P10-B2: Build Zone Progress Components

Implementation status: **Implemented.** Zone progress cards use backend actuals, targets, percent complete, remaining minutes, exceeded state, and central HR-zone colors.

For each zone show:

- Zone label.
- Actual minutes.
- Target minutes.
- Percent complete.
- Remaining minutes.
- Exceeded state.
- Color-coded progress bar.

Acceptance criteria:

- Uses central HR-zone color map.
- Zero target is handled gracefully.
- Over-target state looks positive, not broken.

## P10-B3: Build Session Progress Components

Implementation status: **Implemented.** Cardio and strength session target cards read completed/target/remaining values from backend metrics.

Show:

- Cardio sessions completed vs target.
- Strength sessions completed vs target.
- Total training time.
- Optional unknown/other count if useful.

Acceptance criteria:

- Cardio/strength session progress is clear.
- Unknown classification does not silently disappear if it matters.

## P10-B4: Build Recovery Snapshot

Implementation status: **Implemented.** Recovery and strain snapshot reads weekly averages from backend metrics and handles missing values calmly.

Show:

- Average recovery score for current week.
- Average daily strain for current week.
- Simple state text such as `not enough data yet`, `steady`, or `watch load` only if derived transparently.

Acceptance criteria:

- Missing recovery data renders calm empty state.
- No medical or overconfident coaching language.

## P10-B5: Build Manual Refresh Flow

Implementation status: **Implemented.** Dashboard calls sync status/run APIs, prevents duplicate refresh while pending, and invalidates dashboard/sync queries after refresh.

States:

- Idle.
- Starting.
- Running.
- Success.
- Partial success.
- Failed.

Behavior:

1. User clicks Refresh.
2. Frontend calls sync run endpoint.
3. Frontend polls sync status while running.
4. On completion, dashboard queries invalidate/refetch.
5. Error details are visible but not scary.

Acceptance criteria:

- Refresh button cannot accidentally spam concurrent sync runs.
- Last successful sync stays visible.
- Failure tells the user what to try next.

---

# P11: Goals and Settings Frontend

Implementation status: **Implemented on 2026-04-17.** Settings page is functional for WHOOP status/actions, athlete profile form, and app preference toggling. Goals page is wired to active/history/create goal APIs with editable targets and history.

## Goal

Let the user edit targets and app settings safely from the UI without touching code.

## Dependencies

- `P7`
- `P9`
- `P10` optional

## Outputs

- Goals page.
- Goal edit form.
- Goal history table.
- Settings page.
- WHOOP connection controls.

## P11-B1: Build Goals Page

Implementation status: **Implemented.** Goals page shows active targets, editable HR-zone/cardio/strength form, Monday effective date, save feedback, and API-backed history.

Sections:

- Active goal summary.
- Weekly zone goal form.
- Cardio and strength target fields.
- Effective-date choice.
- Save confirmation.
- Goal history.

Acceptance criteria:

- User can edit targets quickly.
- Midweek behavior is explicit.
- Invalid targets show inline validation.
- Goal history makes it clear old weeks keep old targets.

## P11-B2: Build Goal History Table

Implementation status: **Implemented.** Goal history table shows effective date, key targets, creation timestamp, and current active marker.

Columns:

- Effective from.
- Effective to.
- Zone targets.
- Cardio target.
- Strength target.
- Created reason.
- Created at.

Acceptance criteria:

- History is readable but not overwhelming.
- Current active row is visually marked.

## P11-B3: Build Settings Page

Implementation status: **Implemented.** Settings page shows WHOOP connection state/actions, athlete profile fields, auto-sync toggle, and app preferences backed by server validation.

Sections:

- WHOOP connection status.
- Athlete profile: gender, age or date of birth, height, weight, training focus, and AI notes.
- Auto-sync preference.
- Export preferences.
- App info/version.
- Data maintenance links or placeholders.

Acceptance criteria:

- User can connect/reconnect/disconnect WHOOP.
- User can edit athlete profile context.
- Auto-sync preference can be edited.
- Settings updates use server validation.

---

# P12: Recovery and Strain Insights Frontend

Implementation status: **Implemented on 2026-04-17.** Recovery and strain page uses backend trend datasets, simple chart-like visualizations, four-week comparison cards, deterministic interpretation text, and calm empty states.

## Goal

Create a focused page for weekly recovery/strain trends, rolling windows, and simple interpretation.

## Dependencies

- `P8`
- `P9`
- `P3`

## Outputs

- Recovery & Strain page.
- Trend charts.
- Rolling window cards.
- Interpretation panel.

## P12-B1: Build Trend Chart Components

Implementation status: **Implemented.** Weekly recovery and strain visualizations use backend-provided series and text summaries.

Charts:

- Weekly average recovery.
- Weekly average daily strain.
- 4-week rolling recovery.
- 4-week rolling strain.
- Recovery per strain unit if enough data exists.

Acceptance criteria:

- Charts use backend-provided series.
- Tooltips explain units.
- Insufficient data renders helpful empty states.

## P12-B2: Build Rolling Window Cards

Implementation status: **Implemented.** Rolling comparison cards show current/previous four-week averages, delta direction, and insufficient-history state.

Cards:

- Last 4 weeks recovery average.
- Previous 4 weeks recovery average.
- Last 4 weeks strain average.
- Previous 4 weeks strain average.
- Directional comparison.

Acceptance criteria:

- Comparisons are mathematically simple and transparent.
- UI avoids pseudo-scientific confidence.

## P12-B3: Build Interpretation Panel

Implementation status: **Implemented.** Rule-based interpretation text comes from backend metrics and avoids medical advice.

Initial non-AI interpretation examples:

- `Recovery is steady while training load is rising.`
- `Not enough recovery data yet for a trend.`
- `Strain is up over the last 4 weeks; compare against sleep and recovery before increasing targets.`

Acceptance criteria:

- Text is deterministic and rule-based.
- Text avoids medical advice.
- Text can later be replaced or augmented by AI.

---

# P13: 6-Month Report Page and CSV Export

Implementation status: **Implemented on 2026-04-17.** Report page consumes one backend dataset endpoint and exports CSV from the matching backend dataset.

## Goal

Build long-term training review and export using the shared report dataset builder.

## Dependencies

- `P8`
- `P9`
- `P3`

## Outputs

- 6-month report page.
- Monthly charts.
- Consistency cards.
- CSV export endpoint and button.

## P13-B1: Build Report Page Layout

Implementation status: **Implemented.** Report page includes date range, monthly volume, zone distribution, month details, consistency cards, and export action.

Sections:

1. Date range header.
2. Monthly training volume chart.
3. Monthly zone distribution chart.
4. Cardio vs strength session count chart.
5. Recovery trend chart.
6. Strain trend chart.
7. Consistency cards.
8. Export actions.

Acceptance criteria:

- Report page uses one dataset endpoint.
- Page communicates long-term patterns clearly.
- Charts remain readable on desktop.

## P13-B2: Implement CSV Export Backend

Implementation status: **Implemented.** CSV export uses `SixMonthReportMetricsService`, stable headers, content disposition filename, and backend tests.

CSV should include:

- Date range metadata.
- Monthly training summary rows.
- Zone minutes by month.
- Cardio sessions.
- Strength sessions.
- Average recovery.
- Average strain.
- Consistency summary where appropriate.

Acceptance criteria:

- Export uses same dataset builder as report page.
- CSV headers are stable.
- Numeric values match UI dataset.
- Tests verify CSV ordering and headers.

## P13-B3: Build Export UI

Implementation status: **Implemented.** Report page starts CSV download from the backend export endpoint and shows loading/error states.

Behavior:

- User clicks export.
- Download starts.
- Button shows loading state.
- Errors are clear.

Acceptance criteria:

- Export works from browser.
- Export filename includes date range.
- Empty report exports a valid CSV with headers and metadata.

---

# P14: Testing, Data Integrity, and Reliability Hardening

Implementation status: **Implemented for Version 1 local gates on 2026-04-17.** Backend tests cover health, settings/profile validation/persistence, WHOOP OAuth/token encryption, canonical repositories, annotations, goals, sync, metrics, reports, CSV, API contracts, and integrity checks. Frontend Vitest coverage exists for dashboard, goals, and report rendering. Live E2E remains a manual launch gate.

## Goal

Make the app trustworthy by testing the parts most likely to silently corrupt understanding: sync, transformations, goals, metrics, and exports.

## Dependencies

- `P6`
- `P7`
- `P8`
- `P13`

## Outputs

- Backend unit tests.
- Backend integration tests.
- Frontend component tests.
- Minimal end-to-end tests.
- Data integrity checks.

## P14-B1: Add High-Priority Backend Unit Tests

Implementation status: **Implemented.** Backend tests cover current-week aggregation, rolling recovery/strain, consistency metrics, report datasets, CSV headers, repositories, sync, and provider transformations.

Test areas:

- Zone total aggregation.
- Remaining minutes logic.
- Percent complete logic.
- Goal profile resolution.
- Workout classification.
- Date bucket derivation.
- Rolling averages.
- Consistency metrics.
- WHOOP payload transformation.

Acceptance criteria:

- Golden fixtures exist.
- Formula tests are easy to read.
- Edge cases are covered.

## P14-B2: Add Sync Integration Tests

Implementation status: **Implemented for local gates.** Existing sync orchestrator/API tests cover idempotent windows, provider updates, partial failures, audit counts, and retry/client behavior with mocked provider paths.

Scenarios:

- Same record fetched twice is unchanged.
- Record fetched later with newer `updated_at` updates once.
- Record with same `updated_at` but changed payload hash updates once.
- Pending record later becomes scored.
- Partial page failure does not advance watermark.
- 429 retries.
- 500 retries.
- Malformed single payload is counted and does not corrupt full run.

Acceptance criteria:

- Sync is idempotent under repeated windows.
- Provider updates are reflected.
- Sync audit counts are accurate.

## P14-B3: Add API Contract Tests

Implementation status: **Implemented for Version 1 routes.** API tests cover current week, recovery/strain trends, goal active/history/create, sync status/run, six-month report, and CSV export.

Endpoints:

- Current week summary.
- Recent trends.
- Goal active/history/create.
- Sync status/run.
- Six-month report.
- CSV export.

Acceptance criteria:

- Response shapes are stable.
- Invalid input is rejected with helpful errors.

## P14-B4: Add Frontend Tests

Implementation status: **Implemented.** Vitest and Testing Library cover dashboard populated state, goal form/history rendering, and report populated/export UI rendering.

Test areas:

- Dashboard empty state.
- Dashboard populated state.
- Refresh button state machine.
- Goal form validation.
- Report page empty/populated state.
- API error rendering.

Acceptance criteria:

- Component tests cover main branches.
- TypeScript build catches API type mismatch.

## P14-B5: Add Minimal End-to-End Tests

Implementation status: **Documented as manual live launch gate.** Local route smoke checks passed for dashboard, goals, recovery/strain, report, settings, and the new backend endpoints; live WHOOP/deploy E2E remains in the launch checklist.

Happy paths:

1. Dashboard loads.
2. Manual refresh path renders running/success state with mocked backend or seeded local backend.
3. Goal update path works.
4. CSV export downloads.

Acceptance criteria:

- E2E suite is small and maintainable.
- It catches broken critical flows without becoming slow and brittle.

## P14-B6: Add Data Integrity Checks

Implementation status: **Implemented.** `python -m app.jobs.check_integrity` checks goal overlaps, invalid durations, absurd zone totals, orphan annotations, and missing sync state.

Checks:

- Overlapping goal profiles.
- End time before start time.
- Negative durations.
- Absurd zone totals.
- Orphan workout annotations.
- Missing sync state rows.

Acceptance criteria:

- Integrity command exists.
- Runbook explains what failures mean.

---

# P15: Deployment, Scheduled Sync, Backups, and Runbooks

Implementation status: **Implemented for local deployment planning on 2026-04-17.** Docker Compose artifacts, env template, scheduled sync example, SQLite-safe backup script, integrity command, and runbooks exist. Actual private server deployment and restore validation remain manual launch gates.

## Goal

Make the app deployable and maintainable on a private server with persistent SQLite, scheduled sync, and reliable backups.

## Dependencies

- `P2`
- `P6`
- `P13`
- `P14` strongly recommended

## Outputs

- Dockerfile or deployment scripts.
- Persistent volume layout.
- Systemd/cron sync config.
- Backup script.
- Restore runbook.
- Deployment runbook.

## P15-B1: Create Production Build Strategy

Implementation status: **Implemented.** Production uses a backend container plus lightweight frontend container serving built static assets behind private localhost/Tailscale access.

Preferred setup:

- Build frontend into static assets.
- Serve static frontend from backend or lightweight production server.
- Run FastAPI behind private network/reverse proxy.
- Use one persistent volume for SQLite and backups.

Acceptance criteria:

- `make build` produces deployable artifact.
- Production config does not require frontend dev server.
- Static assets load correctly.

## P15-B2: Add Docker/Container Setup

Implementation status: **Implemented.** `Dockerfile`, `deploy/frontend.Dockerfile`, `deploy/docker-compose.yml`, `deploy/nginx.conf`, and `deploy/env.example` exist.

Files:

- `Dockerfile`
- `deploy/docker-compose.yml` if useful
- `deploy/env.example`

Acceptance criteria:

- Container starts backend.
- Built frontend is served.
- Database volume persists across restarts.
- App runs as non-root where practical.

## P15-B3: Configure Private Access

Implementation status: **Implemented in runbooks.** Deployment docs bind the web service to localhost by default for private reverse proxy/Tailscale exposure.

Recommended:

- Bind app to private network interface or localhost behind Tailscale/reverse proxy.
- Do not expose directly to public internet.
- Add optional basic auth only if needed.

Acceptance criteria:

- Runbook states exact access model.
- Public exposure is not accidental.
- Secrets remain server-side.

## P15-B4: Add Scheduled Sync

Implementation status: **Implemented.** `deploy/scheduled-sync.cron.example` documents scheduled invocation of `python -m app.jobs.run_sync --trigger scheduled`.

Options:

- Systemd timer.
- Cron job.

Command:

```bash
python -m app.jobs.run_sync --trigger scheduled
```

Acceptance criteria:

- Scheduled sync calls backend job with correct env.
- Logs are written somewhere inspectable.
- Sync does not run concurrently with itself.

## P15-B5: Add Backup Script

Implementation status: **Implemented.** `scripts/sqlite_backup.py` uses SQLite backup APIs and optional retention pruning.

Backup requirements:

- Daily SQLite backup.
- Use SQLite-safe backup method.
- Include retention, such as daily for 14 days and weekly for 8 weeks.
- Store off-server or encrypted if possible.
- Document restore.

Acceptance criteria:

- Backup command works.
- Restore command is documented and tested on a copy.
- Runbook says where backups live.

## P15-B6: Add Runbooks

Implementation status: **Implemented.** Deployment, backup, restore, rotate secrets, replay sync, connect WHOOP, update/rollback, operations checklist, launch checklist, and AI handoff runbooks exist.

Create:

- `docs/runbooks/deploy.md`
- `docs/runbooks/backup.md`
- `docs/runbooks/restore.md`
- `docs/runbooks/rotate-secrets.md`
- `docs/runbooks/replay-sync.md`
- `docs/runbooks/connect-whoop.md`
- `docs/runbooks/update-and-rollback.md`
- `docs/runbooks/operations-checklist.md`
- `docs/runbooks/ai-integration-handoff.md`

Acceptance criteria:

- A future AI coding agent can deploy/update without rediscovering decisions.
- Restore process is explicit.
- Replay sync process includes choosing date windows safely.

## P15-B7: Add Operations Checklist

Implementation status: **Implemented.** `docs/runbooks/operations-checklist.md` covers health checks, sync, backup, disk, logs, migrations, WHOOP status, and smoke URLs.

Checklist must cover:

- Current app URL and access path.
- Container/service status.
- Latest app version or git commit.
- Last successful scheduled sync time.
- Latest backup timestamp.
- Disk space for app volume and backup volume.
- Log locations.
- Migration status.
- WHOOP connection status.
- Basic smoke URLs.

Acceptance criteria:

- A non-expert can tell whether the app is healthy in under 10 minutes.
- The checklist includes exact commands for the chosen server setup.
- The checklist does not expose secrets.

## P15-B8: Document Server Inventory and Local AI Availability

Implementation status: **Implemented as handoff template.** `docs/runbooks/ai-integration-handoff.md` records the server inventory and AI availability fields without storing secrets.

Purpose:

- Capture what is already installed on the private server before AI work begins.
- Specifically check whether OpenClaw is installed, how it is exposed, and whether it offers an OpenAI-compatible HTTP API.
- Record whether the fallback AI path is ChatGPT/OpenAI API, another hosted model, or no AI.

Document in `docs/runbooks/ai-integration-handoff.md`:

- Server hostname or friendly name.
- App deployment path.
- Container names or systemd service names.
- Tailscale host/IP or private URL.
- OpenClaw process/container/service name if present.
- OpenClaw base URL, port, auth method, and model names if known.
- Whether outbound internet is allowed from the app container.
- Where AI provider secrets should live.
- Who is responsible for the final manual hookup.

Acceptance criteria:

- Future AI integration work does not require rediscovering the server layout.
- The handoff clearly states whether OpenClaw is ready, needs configuration, or is only assumed to exist.
- The document avoids storing real API keys or tokens.

---

# P16: UX Polish, Empty States, Responsive Pass, and Launch Checklist

Implementation status: **Implemented for local gates on 2026-04-17.** Core placeholder pages have been replaced, empty/error/loading states are calmer, responsive layouts use stacked grids and scrollable tables, focus styles remain visible, and launch checklist exists.

## Goal

Turn the functional app into something the user actually wants to use repeatedly.

## Dependencies

- `P10`
- `P11`
- `P12`
- `P13`

## Outputs

- Polished UI states.
- Better loading/error/empty states.
- Responsive pass.
- Accessibility pass.
- Launch checklist.

## P16-B1: Polish Dashboard Visual Hierarchy

Implementation status: **Implemented.** Dashboard prioritizes weekly training, sessions, HR-zone progress, recovery/strain snapshot, and sync status.

Check:

- The weekly progress answer is immediate.
- HR-zone colors are consistent.
- Remaining volume is visually prominent.
- Sync status is visible but not distracting.
- Cards have rhythm and spacing.
- Charts do not overpower core metrics.

Acceptance criteria:

- Dashboard passes the 10-second understanding test.
- No obvious placeholder UI remains.

## P16-B2: Polish Empty States

Implementation status: **Implemented.** Core pages render calm empty states for no data, missing history, unavailable APIs, and export/sync failures.

Empty states:

- No WHOOP connected.
- Connected but no sync yet.
- Sync failed.
- No workouts this week.
- No recovery data yet.
- Not enough history for rolling trend.
- No report data.

Acceptance criteria:

- Empty states explain next action.
- Empty states are calm and not accusatory.

## P16-B3: Responsive Pass

Implementation status: **Implemented for local gates.** Grids stack at narrow widths, navigation wraps, tables scroll horizontally, and charts use responsive columns.

Targets:

- Desktop is excellent.
- Tablet is good.
- Mobile is usable but not primary.

Acceptance criteria:

- Navigation works on narrow widths.
- Cards stack cleanly.
- Charts do not overflow.
- Forms remain usable.

## P16-B4: Accessibility Pass

Implementation status: **Implemented for local gates.** Forms have labels, focus states are visible, buttons have text labels, color is paired with text, and chart sections include text summaries/tooltips.

Check:

- Keyboard navigation.
- Visible focus states.
- Color contrast.
- Button labels.
- Chart fallback labels or summaries.
- Form labels and errors.

Acceptance criteria:

- Core flows can be completed with keyboard.
- Text contrast is acceptable.
- Color is not the only indicator of progress/error.

## P16-B5: Launch Checklist

Implementation status: **Implemented.** `docs/runbooks/launch-checklist.md` separates completed local gates from manual live gates.

Checklist:

- Local tests pass.
- Build passes.
- Migrations apply from empty DB.
- Migrations apply to existing DB copy.
- WHOOP connect works.
- Manual sync works.
- Dashboard loads with real data.
- Goals can be edited.
- Report page loads.
- CSV export works.
- Backup runs.
- Restore tested on copy.
- Secrets are not committed.
- App is private-only.

Acceptance criteria:

- Launch checklist is completed and checked into docs or release notes.

---

# P17: Version 1.5 Expansion: Tags, Notes, Strength Splits

Implementation status: **Implemented on 2026-04-17.** Recent workouts API, annotation update API, Training Log UI, manual tags/notes/classification/strength split editing, strength overview metrics, and backend/frontend tests exist.

## Goal

Add manual context without corrupting imported WHOOP facts.

## Dependencies

- Version 1 core complete

## Outputs

- Workout annotations UI.
- Manual tags.
- Notes.
- Strength split labels.
- Filter/report support.

## P17-B1: Add Workout Annotation API

Implementation status: **Implemented.** `GET /api/v1/workouts/recent`, `PATCH /api/v1/workouts/{id}/annotation`, annotation validation/normalization, and API tests exist.

Route:

- `PATCH /api/v1/workouts/{id}/annotation`

Fields:

- Manual strength split: upper, lower, full, unknown/null.
- Manual tag.
- Notes.

Acceptance criteria:

- Annotation is stored separately.
- Annotation survives provider update.
- Empty notes are handled cleanly.

## P17-B2: Add Annotation UI

Implementation status: **Implemented.** Training Log page shows recent workouts and supports inline manual context editing.

Locations:

- Workout detail drawer or table.
- Strength overview section.
- Report filters later if useful.

Acceptance criteria:

- User can tag workouts without friction.
- UI makes clear this is manual context.

## P17-B3: Add Strength Overview

Implementation status: **Implemented.** Strength overview API and Training Log summary cards show strength sessions, split counts, untagged sessions, and strength strain.

Metrics:

- Strength sessions per week/month.
- Upper/lower/full counts if tagged.
- Strength strain contribution.

Acceptance criteria:

- Untagged strength sessions are visible.
- Manual classification improves but does not block reporting.

---

# P18: Future AI Interpretation Layer and Integration Handoff

Implementation status: **Implemented for local gates on 2026-04-17.** Disabled-by-default AI config, context builder, provider adapter boundary, OpenAI-compatible adapter, status/summary/suggestion APIs, dashboard summary panel, Settings status UI, draft-only goal suggestion flow, and tests exist. Real provider configuration and smoke testing remain manual gates.

## Goal

Add AI-generated summaries and suggestions after the data foundation is trustworthy, with a clear provider boundary for either local OpenClaw or ChatGPT/OpenAI-style APIs.

## Dependencies

- Stable `P8` report dataset builder.
- Stable dashboard/report APIs.
- Stable private deployment from `P15`.
- User decision to use local OpenClaw, ChatGPT/OpenAI API, another compatible provider, or no AI.

## Outputs

- AI integration handoff runbook.
- Provider adapter interface.
- Provider-specific config placeholders.
- Read-only AI summary service.
- Prompt templates.
- Guardrails.
- UI panel.
- Optional suggestion review flow.

## P18-B0: Pause for Integration Walkthrough

This is a mandatory human handoff gate before any AI provider is connected.

The coding agent must walk the user through:

- Where the app is in the build: completed phases, deployed URL, current server setup, sync status, and known gaps.
- Where the relevant code lives: metrics services, report dataset builder, API routes, frontend AI panel location, config/env files, and deployment files.
- The goal of the AI integration: read derived training summaries, produce advisory text, and never touch WHOOP tokens or canonical facts.
- The chosen provider path: local OpenClaw if it is already available on the server, or ChatGPT/OpenAI API if the user chooses hosted AI.
- Exactly what the other AI assistant needs to help with: verifying provider base URL/auth/model, adding secrets to the server, testing one request, and confirming the app can reach the provider.
- What must not be changed: WHOOP OAuth, token storage, sync engine, canonical fact tables, backup process, and goal mutation rules.

Acceptance criteria:

- `docs/runbooks/ai-integration-handoff.md` contains the walkthrough in plain step-by-step language.
- The user understands the integration target before involving another AI.
- The handoff names the exact files and env vars involved.
- No provider key, bearer token, WHOOP token, or private secret is pasted into the document.

## P18-B1: Define AI Boundaries

Implementation status: **Implemented.** AI receives derived context only, remains disabled by default, and disabled/failure states are covered by API behavior/tests.

Rules:

- AI receives structured weekly/monthly summaries.
- AI does not receive WHOOP tokens.
- AI does not query raw tables directly.
- AI does not mutate imported facts.
- AI does not silently mutate goals.
- AI suggestions are advisory and reviewable.
- AI does not provide medical advice.
- AI provider failures do not break dashboard, reports, sync, export, or settings.
- AI can be fully disabled with configuration.

Acceptance criteria:

- AI boundary is documented before implementation.
- Prompt inputs are compact and structured.
- Tests prove disabled AI returns a calm unavailable state.

## P18-B2: Build AI Context Builder

Implementation status: **Implemented.** Context builder uses current-week metrics, six-month report dataset, recent goals, athlete profile context, sync freshness, app version, and generated timestamp without raw payloads/secrets.

Inputs:

- Current week summary.
- Last 6-month report dataset.
- Recent goal history.
- Athlete profile context when present.
- Sync freshness metadata.
- App version and generated-at timestamp.

Outputs:

- Compact JSON context for AI.
- Stable context schema version.

Acceptance criteria:

- AI context can be generated without network calls.
- Context excludes secrets and raw provider payloads.
- Context is small enough to inspect in logs after redaction.
- Snapshot tests cover empty data, normal data, and stale-sync data.

## P18-B3: Create AI Provider Adapter Boundary

Implementation status: **Implemented.** Provider boundary, disabled provider, and OpenAI-compatible adapter exist. `openclaw` is accepted as configuration but uses the compatible adapter until its exact API is confirmed.

Recommended backend structure:

```text
backend/app/services/ai/
├─ context_builder.py
├─ prompts.py
├─ provider.py
├─ providers/
│  ├─ openclaw.py
│  └─ openai_compatible.py
├─ summary_service.py
└─ types.py
```

Provider config:

```bash
AI_ENABLED=false
AI_PROVIDER=disabled
AI_BASE_URL=
AI_MODEL=
AI_API_KEY=
AI_TIMEOUT_SECONDS=30
AI_MAX_INPUT_TOKENS=12000
AI_MAX_OUTPUT_TOKENS=1200
```

Provider options:

- `disabled`: default; no network calls.
- `openclaw`: local/private server provider, preferred if already installed and reachable.
- `openai_compatible`: hosted or local provider using ChatGPT/OpenAI-compatible chat completions or responses API semantics.

Acceptance criteria:

- The app can boot with `AI_ENABLED=false` and no AI secrets.
- Provider-specific code is isolated behind one interface.
- OpenClaw and ChatGPT/OpenAI-style integrations share the same context builder and prompt templates.
- Errors are normalized so the UI can show `AI unavailable` without exposing internals.
- Provider request and response logs redact prompts if they contain personal training data, unless explicitly enabled for local debugging.

## P18-B4: Build Weekly Summary Generation

Implementation status: **Implemented for explicit user-triggered API/UI flow.** Weekly summary requests are advisory and gracefully return disabled/error states.

Possible outputs:

- This week progress summary.
- Remaining work summary.
- Recovery/strain observation.
- Target realism note.
- Suggested questions for user reflection.

Acceptance criteria:

- Output is clearly advisory.
- Output references data points traceably.
- User can disable AI panel.

## P18-B5: Build AI API and Frontend Panel

Implementation status: **Implemented.** AI status, weekly summary, and goal suggestion APIs exist; Dashboard and Settings include AI surfaces that do not block core app rendering.

Routes:

- `GET /api/v1/ai/status`
- `POST /api/v1/ai/weekly-summary`
- `POST /api/v1/ai/goal-suggestions`

Frontend:

- Dashboard AI summary panel.
- Settings AI status and enablement note.
- Loading, disabled, unavailable, and error states.

Acceptance criteria:

- AI status clearly distinguishes disabled, configured, reachable, and failing.
- Dashboard still renders when AI is disabled or failing.
- AI requests are explicit user-triggered in the first version, not automatic on every page load unless later approved.
- The UI labels AI output as advisory.

## P18-B6: Build Goal Suggestions Safely

Implementation status: **Implemented.** Suggestions are draft-only and can only be loaded into the normal Goals form; accepting still requires the existing goal creation flow.

Rules:

- AI can suggest target changes.
- User must explicitly accept any goal change.
- Accepted changes create normal versioned goal profile rows.
- Suggestions include rationale and confidence language.
- Suggested changes are shown as a draft diff before save.
- Rejected suggestions are not persisted unless a future review log is intentionally added.

Acceptance criteria:

- No automatic goal mutation.
- Suggestions preserve historical goal truth.
- Tests prove suggestions cannot bypass the normal goal creation API.

## P18-B7: Verify Provider Integration

Implementation status: **Partially implemented/local gates passed.** Disabled boot/status and graceful failure behavior are tested locally. Real provider configuration, health request, real summary request, and log inspection remain manual gates.

Verification steps:

1. Confirm `AI_ENABLED=false` boot still works.
2. Confirm `/api/v1/ai/status` reports disabled cleanly.
3. Configure local OpenClaw if selected, or ChatGPT/OpenAI-compatible env vars if selected.
4. Run one provider health request from the server.
5. Run one AI summary request with a fixture context.
6. Run one AI summary request with real derived metrics.
7. Confirm no WHOOP token, refresh token, raw payload, or API key appears in logs.
8. Confirm dashboard/report/export still work if the provider is shut off.

Acceptance criteria:

- Integration has a repeatable smoke test.
- Failure mode is graceful.
- The handoff runbook records the exact working provider settings without secrets.

---

# Cross-Cutting Implementation Notes

## Time and Date Rules

- Store event timestamps in UTC.
- Store local date buckets during import.
- Use ISO weeks with Monday start everywhere.
- Use seconds for stored durations.
- Convert to minutes for display and export.
- Include timezone assumptions in docs.

## Sync Rules

- Sync windows must be safe to repeat.
- Use overlap for incremental sync.
- Upsert by external ID or cycle ID.
- Preserve annotations during upsert.
- Advance watermarks only after successful commit.
- Missing records in a later window are not delete signals.
- Pending or unscorable provider records can be stored and updated later.

## Security Rules

- WHOOP secrets stay server-side.
- WHOOP tokens are encrypted at rest.
- Tokens are never logged.
- App should be private-network-only by default.
- Backups should be encrypted or stored securely.
- No real secrets in git.
- AI providers receive only derived summaries, never WHOOP tokens or raw provider payloads.
- AI provider keys live only in server env/config, never frontend code.

## UI Rules

- Backend owns formulas.
- Frontend owns presentation.
- Frontend should not recompute progress percentages.
- Empty states are first-class UI.
- The dashboard should prioritize clarity over completeness.
- Color should communicate but not be the only information channel.

## Testing Priorities

The highest-value tests are:

1. Sync idempotency.
2. Provider update handling.
3. Goal profile resolution.
4. Weekly zone aggregation.
5. Remaining minutes calculation.
6. 6-month dataset consistency.
7. CSV export matching report dataset.
8. Token refresh behavior.

## Suggested Build Order for Actual Execution

When ready to start coding, follow this order:

1. `P0`: Lock defaults and docs.
2. `P1`: Create repo skeleton.
3. `P2`: Backend shell and database baseline.
4. `P3`: Frontend shell and visual direction.
5. `P5`: Schema models before real sync.
6. `P4`: WHOOP OAuth.
7. `P6`: Sync engine.
8. `P7`: Goals/settings.
9. `P8`: Metrics.
10. `P9`: APIs and typed contracts.
11. `P10`: Dashboard.
12. `P11`: Goals/settings UI.
13. `P12`: Recovery/strain UI.
14. `P13`: Report/export.
15. `P14`: Hardening tests.
16. `P15`: Deployment/backups.
17. `P16`: Polish and launch.
18. `P17`: Manual tags/notes.
19. `P18-B0`: AI integration walkthrough and handoff.
20. `P18`: AI layer.

This differs slightly from the phase numbering because schema work can productively happen before OAuth once the backend foundation exists. The phase IDs remain stable, but execution can intentionally reorder independent pieces when it saves time.

## Milestone Definitions

## Milestone M1: Empty App Boots

Included phases:

- `P0`
- `P1`
- `P2`
- `P3`

Done when:

- Backend boots.
- Frontend boots.
- Health endpoint works.
- Placeholder pages render.
- Design direction is visible.

## Milestone M2: Data Can Land

Included phases:

- `P4`
- `P5`
- `P6`

Done when:

- WHOOP connects.
- Tokens are secure.
- Initial backfill imports facts.
- Manual sync works.
- Sync audit trail exists.

## Milestone M3: Product Becomes Useful

Included phases:

- `P7`
- `P8`
- `P9`
- `P10`

Done when:

- Goals are editable.
- Current week summary works.
- Dashboard shows progress and remaining work.
- Manual refresh updates dashboard data.

## Milestone M4: Product Becomes Reviewable

Included phases:

- `P11`
- `P12`
- `P13`

Done when:

- Goals/settings UI is complete.
- Recovery/strain trends are visible.
- 6-month report works.
- CSV export works.

## Milestone M5: Product Becomes Dependable

Included phases:

- `P14`
- `P15`
- `P16`

Done when:

- Tests cover core risk areas.
- App deploys privately.
- Backups and restore are documented.
- UI polish is good enough for repeated personal use.

## Milestone M6: AI Is Ready to Hook Up

Included phases:

- `P18-B0`
- `P18-B1`
- `P18-B2`
- `P18-B3`

Done when:

- The user has a step-by-step AI integration handoff.
- The app exposes a clean AI provider boundary.
- OpenClaw versus ChatGPT/OpenAI provider choice is documented.
- AI can remain disabled without affecting the full Version 1 app.

## Milestone M7: AI Is Live and Safe

Included phases:

- `P18-B4`
- `P18-B5`
- `P18-B6`
- `P18-B7`

Done when:

- AI summaries work from derived metrics.
- Goal suggestions are review-only until explicitly accepted.
- Provider failure is graceful.
- No secrets or raw WHOOP payloads are sent to the model.

## Final End State

At the end of this Markdown plan, Version 1 should be through: a private WHOOP-connected dashboard that imports training, sleep, and recovery data; stores it cleanly; calculates weekly and monthly progress against editable goals; shows remaining work; visualizes recovery and strain trends; exports a 6-month report; and runs safely on a private server with backups, scheduled sync, update/rollback runbooks, operations checks, and documented private access.

After Version 1, the AI path should be ready for a deliberate handoff: the app has a read-only AI context builder, a provider adapter boundary, disabled-by-default config, a clear choice between local OpenClaw and ChatGPT/OpenAI-compatible providers, and a step-by-step runbook the user can give to another AI assistant for the final server hookup.
