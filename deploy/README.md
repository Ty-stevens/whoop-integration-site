# Deployment Notes

Version 1 targets Docker Compose on a Tailscale-only private server.

Reference files:

- `Dockerfile`
- `deploy/docker-compose.yml`
- `deploy/env.example`
- `deploy/scheduled-sync.cron.example`
- `scripts/sqlite_backup.py`

The private server layout assumed by the runbooks is:

```text
/opt/endurasync
```
