# Operations Checklist

Use this to confirm the deployment is healthy in under 10 minutes.

## Access

- Current URL: `http://localhost:8080`
- Private access path: Tailscale, localhost port forward, or private reverse proxy

## Service health

```bash
cd /opt/endurasync/deploy
docker compose ps
curl -f http://localhost:8080/health
curl -f http://localhost:8080/api/v1/health
```

## Version

```bash
cd /opt/endurasync
git rev-parse --short HEAD
```

## Sync

```bash
cd /opt/endurasync/deploy
docker compose logs --tail=50 backend
```

Check:

- Last successful sync time.
- Latest sync run status.
- Whether the WHOOP connection is still valid.

## Backups

```bash
ls -lt /opt/endurasync/backups | head
```

Check:

- Latest backup timestamp.
- Enough free space for the next backup.

## Disk

```bash
df -h /opt/endurasync
```

Check:

- Database volume usage.
- Backup volume usage.

## Migrations

```bash
cd /opt/endurasync/backend
.venv/bin/alembic current
```

## Smoke URLs

- `/health`
- `/api/v1/health`
- `/api/v1/sync/status`
- `/api/v1/integrations/whoop/status`
- Dashboard page
- Goals page
- Recovery/Strain page
- Training Log page
- Six-Month Report page
- Settings page
