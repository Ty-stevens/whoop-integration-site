import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func

from app.db.session import SessionLocal
from app.models import (
    GoalProfileModel,
    RecoveryModel,
    SleepModel,
    WorkoutAnnotationModel,
    WorkoutModel,
)
from app.repositories.sync import SyncRepository


@dataclass(frozen=True)
class IntegrityIssue:
    category: str
    message: str


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check EnduraSync data integrity.")
    parser.parse_args(argv)

    with SessionLocal() as db:
        issues = collect_issues(db)

    if not issues:
        print("Integrity check clean.")
        return 0

    print(f"Integrity check found {len(issues)} issue(s):")
    for issue in issues:
        print(f"- [{issue.category}] {issue.message}")
    return 1


def collect_issues(db) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []
    issues.extend(find_overlapping_goals(db))
    issues.extend(find_invalid_durations(db))
    issues.extend(find_absurd_zone_totals(db))
    issues.extend(find_orphan_annotations(db))
    issues.extend(find_missing_sync_state(db))
    return issues


def find_overlapping_goals(db) -> list[IntegrityIssue]:
    rows = (
        db.query(GoalProfileModel)
        .order_by(GoalProfileModel.effective_from_date.asc(), GoalProfileModel.id.asc())
        .all()
    )
    issues: list[IntegrityIssue] = []
    previous = None
    for row in rows:
        if previous is not None:
            previous_end = previous.effective_to_date or date.max
            if row.effective_from_date <= previous_end:
                issues.append(
                    IntegrityIssue(
                        category="goals",
                        message=(
                            "overlap between goal profile "
                            f"{previous.id} ({previous.effective_from_date.isoformat()}.."
                            f"{_format_date(previous.effective_to_date)}) and "
                            f"{row.id} ({row.effective_from_date.isoformat()}.."
                            f"{_format_date(row.effective_to_date)})"
                        ),
                    )
                )
        previous = row
    return issues


def find_invalid_durations(db) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []

    workouts = (
        db.query(
            WorkoutModel.id,
            WorkoutModel.external_id,
            WorkoutModel.start_time_utc,
            WorkoutModel.end_time_utc,
            WorkoutModel.duration_seconds,
        )
        .order_by(WorkoutModel.id.asc())
        .all()
    )
    for row in workouts:
        elapsed_seconds = int((row.end_time_utc - row.start_time_utc).total_seconds())
        if (
            elapsed_seconds <= 0
            or row.duration_seconds <= 0
            or abs(elapsed_seconds - row.duration_seconds) > 60
        ):
            issues.append(
                IntegrityIssue(
                    category="durations",
                    message=(
                        f"workout {row.id} ({row.external_id}) has "
                        f"start={row.start_time_utc.isoformat()} "
                        f"end={row.end_time_utc.isoformat()} "
                        f"duration_seconds={row.duration_seconds}"
                    ),
                )
            )

    sleeps = (
        db.query(
            SleepModel.id,
            SleepModel.external_id,
            SleepModel.start_time_utc,
            SleepModel.end_time_utc,
            SleepModel.sleep_duration_seconds,
        )
        .order_by(SleepModel.id.asc())
        .all()
    )
    for row in sleeps:
        elapsed_seconds = int((row.end_time_utc - row.start_time_utc).total_seconds())
        if (
            elapsed_seconds <= 0
            or row.sleep_duration_seconds <= 0
            or row.sleep_duration_seconds > elapsed_seconds + 300
        ):
            issues.append(
                IntegrityIssue(
                    category="durations",
                    message=(
                        f"sleep {row.id} ({row.external_id}) has "
                        f"start={row.start_time_utc.isoformat()} "
                        f"end={row.end_time_utc.isoformat()} "
                        f"sleep_duration_seconds={row.sleep_duration_seconds}"
                    ),
                )
            )

    return issues


def find_absurd_zone_totals(db) -> list[IntegrityIssue]:
    rows = (
        db.query(
            WorkoutModel.id,
            WorkoutModel.external_id,
            WorkoutModel.duration_seconds,
            WorkoutModel.zone0_seconds,
            WorkoutModel.zone1_seconds,
            WorkoutModel.zone2_seconds,
            WorkoutModel.zone3_seconds,
            WorkoutModel.zone4_seconds,
            WorkoutModel.zone5_seconds,
        )
        .order_by(WorkoutModel.id.asc())
        .all()
    )
    issues: list[IntegrityIssue] = []
    for row in rows:
        zone_total = sum(
            (
                row.zone0_seconds,
                row.zone1_seconds,
                row.zone2_seconds,
                row.zone3_seconds,
                row.zone4_seconds,
                row.zone5_seconds,
            )
        )
        if zone_total > row.duration_seconds + 300:
            issues.append(
                IntegrityIssue(
                    category="zones",
                    message=(
                        f"workout {row.id} ({row.external_id}) has zone_total_seconds={zone_total} "
                        f"against duration_seconds={row.duration_seconds}"
                    ),
                )
            )
    return issues


def find_orphan_annotations(db) -> list[IntegrityIssue]:
    rows = (
        db.query(WorkoutAnnotationModel.id, WorkoutAnnotationModel.workout_id)
        .outerjoin(WorkoutModel, WorkoutAnnotationModel.workout_id == WorkoutModel.id)
        .filter(WorkoutModel.id.is_(None))
        .order_by(WorkoutAnnotationModel.id.asc())
        .all()
    )
    return [
        IntegrityIssue(
            category="annotations",
            message=f"annotation {row.id} points to missing workout_id={row.workout_id}",
        )
        for row in rows
    ]


def find_missing_sync_state(db) -> list[IntegrityIssue]:
    repository = SyncRepository(db)
    resource_checks = [
        ("workouts", WorkoutModel),
        ("sleeps", SleepModel),
        ("recoveries", RecoveryModel),
    ]
    issues: list[IntegrityIssue] = []
    for resource_type, model in resource_checks:
        has_rows = (db.query(func.count(model.id)).scalar() or 0) > 0
        has_state = repository.get_state(resource_type) is not None
        if has_rows and not has_state:
            issues.append(
                IntegrityIssue(
                    category="sync_state",
                    message=f"missing sync_state row for {resource_type} despite existing data",
                )
            )
    return issues


def _format_date(value: date | None) -> str:
    return value.isoformat() if value is not None else "open-ended"


if __name__ == "__main__":
    raise SystemExit(main())
