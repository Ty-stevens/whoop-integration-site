import argparse
from collections.abc import Sequence

from app.db.session import SessionLocal
from app.services.sync.orchestrator import SyncOutcome
from app.services.sync.service import (
    RunResourceType,
    SyncAlreadyRunningError,
    run_manual_sync,
    run_scheduled_sync,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run EnduraSync WHOOP sync.")
    parser.add_argument(
        "--trigger",
        choices=["manual", "scheduled"],
        default="scheduled",
    )
    parser.add_argument(
        "--resource",
        choices=["workouts", "sleeps", "recoveries", "all"],
        default="all",
    )
    args = parser.parse_args(argv)

    with SessionLocal() as db:
        try:
            if args.trigger == "manual":
                outcomes = run_manual_sync(db, resource_type=args.resource)
            else:
                outcomes = run_scheduled_sync(db, resource_type=args.resource)
        except SyncAlreadyRunningError as exc:
            print(f"Sync skipped: {exc}")
            return 1

    print(_summary(args.trigger, args.resource, outcomes))
    return 1 if outcomes and all(outcome.status == "failed" for outcome in outcomes) else 0


def _summary(trigger: str, resource: RunResourceType, outcomes: Sequence[SyncOutcome]) -> str:
    if not outcomes:
        return f"Sync {trigger}/{resource}: no resources requested."
    status = _aggregate_status(outcomes)
    inserted = sum(outcome.counts.inserted for outcome in outcomes)
    updated = sum(outcome.counts.updated for outcome in outcomes)
    unchanged = sum(outcome.counts.unchanged for outcome in outcomes)
    failed = sum(outcome.counts.failed for outcome in outcomes)
    return (
        f"Sync {trigger}/{resource}: {status} "
        f"inserted={inserted} updated={updated} unchanged={unchanged} failed={failed}"
    )


def _aggregate_status(outcomes: Sequence[SyncOutcome]) -> str:
    statuses = {outcome.status for outcome in outcomes}
    if statuses == {"success"}:
        return "success"
    if statuses == {"failed"}:
        return "failed"
    return "partial"


if __name__ == "__main__":
    raise SystemExit(main())
