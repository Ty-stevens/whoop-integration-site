# Environment Runbook

Copy `.env.example` to `.env.local` for local reference. The backend reads environment variables from the shell and also attempts to load `.env.local` from the repository root.

Do not commit real secrets.

Development can boot with placeholder WHOOP credentials. Production must provide real secrets for encryption and OAuth before connection work is used.

AI defaults to disabled:

```bash
AI_ENABLED=false
AI_PROVIDER=disabled
```

AI provider keys must remain server-side and must not be exposed to frontend code.

For the private deployment, use `deploy/env.example` as the shape reference and keep the live values in `deploy/env.local` on the host.
