from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta

import pytest

from app.db.session import SessionLocal
from app.models.facts import RecoveryModel, WorkoutModel
from app.repositories.sync import SyncRepository
from app.schemas.goals import GoalProfileCreate
from app.services.goal_service import GoalProfileService, seed_default_goals
from app.services.metrics.current_week import CurrentWeekMetricsService
from app.services.metrics.types import MetricsError
from tests.fact_fixtures import recovery_values, workout_values


def create_workout(db, **overrides) -> WorkoutModel:
    row = WorkoutModel(**workout_values(**overrides))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_recovery(db, **overrides) -> RecoveryModel:
    row = RecoveryModel(**recovery_values(**overrides))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def zone(summary, zone_number: int):
    return next(item for item in summary.zones if item.zone == zone_number)


def test_empty_week_without_goal_returns_zero_targets_and_no_divide_by_zero():
    with SessionLocal() as db:
        summary = CurrentWeekMetricsService(db).build(date(2026, 4, 6))

    assert summary.has_goal_profile is False
    assert summary.goal_profile_id is None
    assert summary.week_end_date == date(2026, 4, 12)
    assert all(item.actual_seconds == 0 for item in summary.zones)
    assert all(item.target_minutes == 0 for item in summary.zones)
    assert all(item.percent_complete is None for item in summary.zones)
    assert summary.cardio_sessions.target == 0
    assert summary.cardio_sessions.percent_complete is None
    assert summary.total_training_seconds == 0
    assert summary.average_recovery_score is None
    assert summary.average_daily_strain is None


def test_empty_week_with_seeded_goal_returns_target_based_remaining_values():
    with SessionLocal() as db:
        seed_default_goals(db, effective_from_date=date(2026, 4, 6))
        summary = CurrentWeekMetricsService(db).build(date(2026, 4, 6))

    assert summary.has_goal_profile is True
    assert zone(summary, 2).target_minutes == 150
    assert zone(summary, 2).remaining_minutes == 150
    assert zone(summary, 2).percent_complete == 0
    assert summary.cardio_sessions.completed == 0
    assert summary.cardio_sessions.target == 3
    assert summary.strength_sessions.target == 2


def test_partial_week_sums_zones_sessions_recovery_and_strain():
    with SessionLocal() as db:
        seed_default_goals(db, effective_from_date=date(2026, 4, 6))
        create_workout(db)
        create_workout(
            db,
            external_id="workout-2",
            payload_hash="hash-2",
            raw_payload_json={"id": "workout-2"},
        )
        workout = db.query(WorkoutModel).filter(WorkoutModel.external_id == "workout-2").one()
        workout.classification = "strength"
        workout.strain = 5.5
        db.commit()
        create_recovery(db)
        create_recovery(db, cycle_id="cycle-2", payload_hash="recovery-hash-2")
        recovery = db.query(RecoveryModel).filter(RecoveryModel.cycle_id == "cycle-2").one()
        recovery.recovery_score = 80
        db.commit()

        summary = CurrentWeekMetricsService(db).build(date(2026, 4, 6))

    assert zone(summary, 1).actual_seconds == 1000
    assert zone(summary, 2).actual_seconds == 4000
    assert summary.total_training_seconds == 7200
    assert summary.cardio_sessions.completed == 1
    assert summary.strength_sessions.completed == 1
    assert summary.average_recovery_score == 76
    assert summary.average_daily_strain == 8


def test_over_target_week_sets_exceeded_and_remaining_zero():
    with SessionLocal() as db:
        service = GoalProfileService(db)
        service.create_profile(
            GoalProfileCreate(
                effective_from_date=date(2026, 4, 6),
                zone2_target_minutes=30,
                cardio_sessions_target=1,
                strength_sessions_target=0,
            )
        )
        create_workout(db)
        summary = CurrentWeekMetricsService(db).build(date(2026, 4, 6))

    assert zone(summary, 2).actual_minutes == 33
    assert zone(summary, 2).target_minutes == 30
    assert zone(summary, 2).remaining_minutes == 0
    assert zone(summary, 2).exceeded is True
    assert zone(summary, 2).percent_complete == 110


def test_zero_target_zone_exceeded_only_when_actual_seconds_are_positive():
    with SessionLocal() as db:
        seed_default_goals(db, effective_from_date=date(2026, 4, 6))
        create_workout(db)
        summary = CurrentWeekMetricsService(db).build(date(2026, 4, 6))

    assert zone(summary, 1).target_minutes == 0
    assert zone(summary, 1).percent_complete is None
    assert zone(summary, 1).exceeded is True
    assert zone(summary, 5).target_minutes == 0
    assert zone(summary, 5).exceeded is True

    with SessionLocal() as db:
        seed_default_goals(db, effective_from_date=date(2026, 4, 13))
        empty = CurrentWeekMetricsService(db).build(date(2026, 4, 13))

    assert zone(empty, 1).exceeded is False


def test_historical_week_resolves_historical_goal_profile():
    with SessionLocal() as db:
        service = GoalProfileService(db)
        service.create_profile(
            GoalProfileCreate(effective_from_date=date(2026, 4, 6), zone2_target_minutes=150)
        )
        service.create_profile(
            GoalProfileCreate(effective_from_date=date(2026, 4, 13), zone2_target_minutes=175)
        )

        first = CurrentWeekMetricsService(db).build(date(2026, 4, 6))
        second = CurrentWeekMetricsService(db).build(date(2026, 4, 13))

    assert zone(first, 2).target_minutes == 150
    assert zone(second, 2).target_minutes == 175


def test_non_monday_input_raises_metrics_error():
    with SessionLocal() as db:
        with pytest.raises(MetricsError, match="Monday ISO week start"):
            CurrentWeekMetricsService(db).build(date(2026, 4, 7))


def test_last_successful_sync_timestamp_comes_from_sync_state():
    sync_time = datetime(2026, 4, 14, 12, tzinfo=UTC)
    with SessionLocal() as db:
        SyncRepository(db).upsert_state(
            resource_type="workouts",
            last_successful_sync_at_utc=sync_time,
            last_window_start_utc=sync_time - timedelta(days=1),
            last_window_end_utc=sync_time,
        )
        summary = CurrentWeekMetricsService(db).build(date(2026, 4, 6))

    assert summary.last_successful_sync_at_utc == sync_time


def test_metrics_output_does_not_include_raw_payloads_or_secrets():
    with SessionLocal() as db:
        seed_default_goals(db, effective_from_date=date(2026, 4, 6))
        create_workout(
            db,
            raw_payload_json={"id": "workout-1", "access_token": "secret"},
        )
        summary = CurrentWeekMetricsService(db).build(date(2026, 4, 6))

    output = str(asdict(summary))
    assert "raw_payload_json" not in output
    assert "access_token" not in output
    assert "refresh_token" not in output
    assert "secret" not in output
