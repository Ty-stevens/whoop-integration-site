import argparse
import os
import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a SQLite-safe EnduraSync backup.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", "sqlite:///./data/endurasync.db"),
    )
    parser.add_argument(
        "--backup-dir",
        default=os.environ.get("BACKUP_DIR", "./backups"),
    )
    parser.add_argument("--retention-days", type=int, default=14)
    parser.add_argument("--retention-weeks", type=int, default=8)
    parser.add_argument("--prune", action="store_true")
    args = parser.parse_args(argv)

    source_path = _sqlite_path(args.database_url)
    backup_dir = Path(args.backup_dir).expanduser()
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"endurasync-{timestamp}.sqlite3"
    _backup_sqlite(source_path, backup_path)
    print(f"Backup created: {backup_path}")

    if args.prune:
        removed = prune_backups(
            backup_dir,
            retention_days=args.retention_days,
            retention_weeks=args.retention_weeks,
        )
        for path in removed:
            print(f"Pruned: {path}")

    return 0


def _sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("DATABASE_URL must point at a SQLite database")
    raw_path = database_url.removeprefix(prefix)
    return Path(raw_path).expanduser().resolve()


def _backup_sqlite(source_path: Path, backup_path: Path) -> None:
    if not source_path.exists():
        raise FileNotFoundError(f"Source database does not exist: {source_path}")
    with sqlite3.connect(source_path) as source, sqlite3.connect(backup_path) as destination:
        source.backup(destination)


def prune_backups(backup_dir: Path, *, retention_days: int, retention_weeks: int) -> list[Path]:
    now = datetime.now(UTC)
    backups = sorted(
        (path for path in backup_dir.glob("*.sqlite3") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    weekly_keep: dict[tuple[int, int], Path] = {}
    removed: list[Path] = []
    daily_cutoff = retention_days * 24 * 60 * 60
    weekly_cutoff = retention_weeks * 7 * 24 * 60 * 60

    for path in backups:
        age_seconds = now.timestamp() - path.stat().st_mtime
        if age_seconds <= daily_cutoff:
            continue
        if age_seconds <= weekly_cutoff:
            key = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isocalendar()[:2]
            weekly_keep.setdefault(key, path)
            continue
        removed.append(path)

    for path in backups:
        if path in removed:
            continue
        age_seconds = now.timestamp() - path.stat().st_mtime
        if age_seconds > daily_cutoff and age_seconds <= weekly_cutoff:
            key = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isocalendar()[:2]
            if weekly_keep.get(key) != path:
                removed.append(path)

    for path in removed:
        path.unlink(missing_ok=True)
    return removed


if __name__ == "__main__":
    raise SystemExit(main())
