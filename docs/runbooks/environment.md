# Environment Runbook

Copy `.env.example` to `.env.local` for local reference. The backend reads environment variables from the shell and also attempts to load `.env.local` from the repository root.

Do not commit real secrets.

Development can boot with placeholder WHOOP credentials. Production must provide real secrets for encryption and OAuth before connection work is used.

Vercel production must also use durable database storage. Do not use the default
SQLite `DATABASE_URL` on Vercel: function storage is ephemeral, so OAuth states,
WHOOP tokens, synced metrics, reports, and benchmarks can disappear between
requests. Use a managed Postgres database such as Neon and set `DATABASE_URL` to
its Postgres connection string. The backend accepts standard `postgres://` or
`postgresql://` URLs and normalizes them for SQLAlchemy.

AI defaults to disabled:

```bash
AI_ENABLED=false
AI_PROVIDER=disabled
```

OpenAI-compatible AI can be enabled server-side with either the generic AI variables or
the OpenAI aliases:

```bash
AI_ENABLED=true
AI_PROVIDER=openai_compatible
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=<model>
OPENAI_API_KEY=<server-side key>
```

AI provider keys must remain server-side and must not be exposed to frontend code. If AI
is enabled but these values are incomplete, the app reports a setup error from `/api/v1/ai/status`
without blocking WHOOP sync, health, or dashboard routes.

For the private deployment, use `deploy/env.example` as the shape reference and keep the live values in `deploy/env.local` on the host.
