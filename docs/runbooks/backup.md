# Backup Runbook

Use the SQLite backup script from the host.

## Manual backup

```bash
cd /opt/endurasync
DATABASE_URL=sqlite:////opt/endurasync/data/endurasync.db \
BACKUP_DIR=/opt/endurasync/backups \
python scripts/sqlite_backup.py --prune
```

The backup is a point-in-time copy made with SQLite's backup API, so it is safe with WAL mode.

## Retention model

- Keep all backups for 14 days.
- Keep one backup per ISO week for the next 8 weeks.
- Delete older backups during pruning.

## Off-server copy

Send the backup directory to the off-server location after the local backup finishes.

```bash
rsync -a /opt/endurasync/backups/ backup-user@backup-host:/srv/backups/endurasync/
```

Do not sync secrets files separately; only the database backup belongs in the backup set.
