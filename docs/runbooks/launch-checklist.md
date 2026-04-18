# Launch Checklist

## Local gates

- `make test`
- `make lint`
- `make build`
- Migrations apply on a fresh database
- Migrations apply on an existing database copy
- Manual WHOOP connect works in development
- Manual sync works in development
- Integrity check is clean on a known-good dataset

## Local status snapshot (2026-04-18)

Locally complete now:

- `make lint` passed
- `make build` passed
- `make integrity` passed
- `make test` passed
- Migrations apply on a fresh database (`DATABASE_URL=sqlite:////tmp/endurasync-migration-fresh.db`)
- Migrations apply on an existing local database copy (`backend/data/endurasync.db`)
- Local smoke checks passed:
  - Backend: `/health`, `/api/v1/health`, `/api/v1/sync/status`
  - Frontend routes: `/dashboard`, `/goals`, `/recovery-strain`, `/training-log`, `/reports/six-month`, `/settings`

Blocked on live WHOOP/server:

- Manual WHOOP connect works in development (requires real OAuth credentials)
- Manual sync works in development with real WHOOP data
- Private deployment URL loads
- `/health` is green on deployed host
- `/api/v1/health` is green on deployed host
- WHOOP connect works in production
- Manual sync works in production
- Dashboard loads real data in production
- Goals can be edited in production
- Report page loads in production
- CSV export works in production
- Backup runs on target host
- Restore is tested on a copy on target host
- Scheduled sync runs once and does not overlap itself
- App is private-only in deployment networking

Blocked on external credentials/providers:

- Real WHOOP OAuth credentials (`WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET`)
- Real production encryption key (`APP_ENCRYPTION_KEY`)
- Optional real AI provider credentials/configuration if AI is enabled

## Manual live gates

- Private deployment URL loads
- `/health` is green
- `/api/v1/health` is green
- WHOOP connect works in production
- Manual sync works in production
- Dashboard loads real data
- Goals can be edited
- Report page loads
- CSV export works
- Backup runs
- Restore is tested on a copy
- Scheduled sync runs once and does not overlap itself
- Secrets are not committed
- App is private-only

## Final sign-off

Do not launch until both lists are complete and the backup plus restore path have been exercised on the live stack.

## Next Actions For Live Launch

1. Fill `deploy/env.local` with non-placeholder `APP_ENCRYPTION_KEY`, WHOOP credentials, and production URLs.
2. Deploy on the private host and verify `/health` plus `/api/v1/health`.
3. Run WHOOP connect and manual sync on the deployed app.
4. Confirm dashboard/goals/report with real data and run CSV export.
5. Execute backup then restore validation on a copy before final launch sign-off.
