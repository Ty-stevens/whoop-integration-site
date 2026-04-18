# Rotate Secrets Runbook

Rotate only from the host password manager and the live env file.

## Secrets in scope

- `APP_ENCRYPTION_KEY`
- `WHOOP_CLIENT_ID`
- `WHOOP_CLIENT_SECRET`

## Rotation steps

1. Update the secret in the password manager.
2. Update `deploy/env.local` on the host.
3. Redeploy the stack.

```bash
cd /opt/endurasync/deploy
docker compose up -d --build
```

## Important note

Changing `APP_ENCRYPTION_KEY` affects the encrypted WHOOP tokens already stored in SQLite. Plan the rotation with a fresh WHOOP reconnect immediately after the new key is active.

## After rotation

1. Verify `/health`.
2. Verify WHOOP connection status.
3. Run a manual sync.
