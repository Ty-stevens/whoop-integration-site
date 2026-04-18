# Restore Runbook

Restore from a known-good SQLite backup copy.

## 1. Stop the stack

```bash
cd /opt/endurasync/deploy
docker compose down
```

## 2. Restore the database file

1. Find the backup you want to restore.
2. Replace the live SQLite file inside the `endurasync-data` volume with that backup.
3. If the database lives on the host instead of a volume, copy the backup back to `data/endurasync.db`.

Example for a host-path restore:

```bash
cp /opt/endurasync/backups/endurasync-YYYYMMDDTHHMMSSZ.sqlite3 /opt/endurasync/data/endurasync.db
```

## 3. Restart and verify

```bash
cd /opt/endurasync/deploy
docker compose up -d --build
curl -f http://localhost:8080/health
curl -f http://localhost:8080/api/v1/health
```

## 4. After restore

- Re-run a manual sync if the backup predates the latest WHOOP data.
- Confirm the dashboard and goals pages load.
- Run the integrity check before declaring success.
