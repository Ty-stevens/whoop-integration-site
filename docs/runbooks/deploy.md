# Deploy Runbook

Target layout:

```text
/opt/endurasync
  deploy/
  data/
  backups/
  logs/
```

## 1. Prepare the host

1. Install Docker Engine and the Compose plugin.
2. Clone the repository to `/opt/endurasync`.
3. Create the working directories: `mkdir -p /opt/endurasync/data /opt/endurasync/backups /opt/endurasync/logs`.
4. Copy `deploy/env.example` to `deploy/env.local`.
5. Fill `deploy/env.local` with real values from the password manager.
6. Keep `APP_ENCRYPTION_KEY`, `WHOOP_CLIENT_ID`, and `WHOOP_CLIENT_SECRET` out of git.

## 2. Start the stack

```bash
cd /opt/endurasync/deploy
docker compose up -d --build
```

## 3. Verify the basics

```bash
curl -f http://localhost:8080/health
curl -f http://localhost:8080/api/v1/health
docker compose ps
```

## 4. First-time setup

1. Open the app through the private URL.
2. Connect WHOOP.
3. Run a manual sync.
4. Seed or confirm goals.
5. Check the dashboard and settings page.

## 5. Notes

- The web container serves the built frontend.
- The backend stores SQLite data in the host bind mount at `/opt/endurasync/data`.
- Scheduled sync should run from the host, not inside the browser session.
