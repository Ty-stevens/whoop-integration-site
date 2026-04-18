# Replay Sync Runbook

Use this when the app needs to fetch a broader slice of WHOOP history again.

## Safe replay order

1. Take a backup first.
2. Pause scheduled sync.
3. Replay one resource at a time.
4. Watch the sync logs for the resource window that was used.

## Manual replay command

```bash
cd /opt/endurasync/deploy
docker compose run --rm backend python -m app.jobs.run_sync --trigger manual --resource workouts
docker compose run --rm backend python -m app.jobs.run_sync --trigger manual --resource sleeps
docker compose run --rm backend python -m app.jobs.run_sync --trigger manual --resource recoveries
```

## Choosing the window

The current job replays the provider's built-in sync window. Before running it, confirm the intended date range from the live data snapshot and the last successful sync time, then replay only the resources that need it. If the replay would overlap with a running sync, stop and resolve that first.

## After replay

- Run the integrity check.
- Confirm the dashboard reflects the expected records.
- Restart scheduled sync.
