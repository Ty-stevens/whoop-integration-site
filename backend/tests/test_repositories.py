from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.repositories.annotations import AnnotationRepository
from app.repositories.goals import GoalRepository
from app.repositories.recoveries import RecoveryRepository
from app.repositories.sleeps import SleepRepository
from app.repositories.sync import SyncRepository
from app.repositories.workouts import WorkoutRepository
from tests.fact_fixtures import recovery_values, sleep_values, workout_values


def test_workout_upsert_insert_update_unchanged_and_date_lookup():
    with SessionLocal() as db:
        repo = WorkoutRepository(db)

        inserted = repo.upsert(workout_values())
        unchanged = repo.upsert(workout_values())
        updated = repo.upsert(
            workout_values(
                external_updated_at_utc=datetime(2026, 4, 1, 12, tzinfo=UTC),
                payload_hash="hash-2",
                raw_payload_json={"id": "workout-1", "changed": True},
            )
        )

        week_rows = repo.list_by_iso_week(date(2026, 4, 6))
        month_rows = repo.list_by_month(date(2026, 4, 1))

    assert inserted.inserted is True
    assert unchanged.unchanged is True
    assert updated.updated is True
    assert updated.row.source_revision == 2
    assert updated.row.raw_payload_json["changed"] is True
    assert len(week_rows) == 1
    assert len(month_rows) == 1


def test_payload_hash_change_updates_even_when_provider_timestamp_matches():
    with SessionLocal() as db:
        repo = WorkoutRepository(db)
        repo.upsert(workout_values())
        updated = repo.upsert(workout_values(payload_hash="different-hash"))

    assert updated.updated is True
    assert updated.row.source_revision == 2


def test_annotations_survive_provider_workout_updates():
    with SessionLocal() as db:
        workouts = WorkoutRepository(db)
        annotations = AnnotationRepository(db)
        workout = workouts.upsert(workout_values()).row
        annotation = annotations.upsert_workout_annotation(
            workout.id,
            manual_classification="strength",
            tag="manual-review",
            notes="Felt more like gym work.",
        )

        workouts.upsert(
            workout_values(
                external_updated_at_utc=datetime(2026, 4, 1, 12, tzinfo=UTC),
                payload_hash="hash-2",
            )
        )
        persisted = annotations.get_for_workout(workout.id)

    assert annotation.id == persisted.id
    assert persisted.manual_classification == "strength"
    assert persisted.notes == "Felt more like gym work."


def test_sleep_and_recovery_uniqueness_constraints_and_queries():
    with SessionLocal() as db:
        sleep_repo = SleepRepository(db)
        recovery_repo = RecoveryRepository(db)

        sleep_repo.upsert(sleep_values())
        recovery_repo.upsert(recovery_values())
        same_sleep = sleep_repo.upsert(sleep_values())
        same_recovery = recovery_repo.upsert(recovery_values())

        duplicate_sleep = sleep_repo.model(**sleep_values())
        duplicate_recovery = recovery_repo.model(**recovery_values())
        db.add(duplicate_sleep)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        db.add(duplicate_recovery)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        sleeps_for_month = sleep_repo.list_by_month(date(2026, 4, 1))
        recoveries_for_week = recovery_repo.list_by_iso_week(date(2026, 4, 6))

    assert same_sleep.unchanged is True
    assert same_recovery.unchanged is True
    assert len(sleeps_for_month) == 1
    assert len(recoveries_for_week) == 1


def test_goal_profile_effective_date_resolution():
    with SessionLocal() as db:
        repo = GoalRepository(db)
        repo.create(
            {
                "effective_from_date": date(2026, 4, 6),
                "effective_to_date": date(2026, 4, 12),
                "zone1_target_minutes": 0,
                "zone2_target_minutes": 150,
                "zone3_target_minutes": 0,
                "zone4_target_minutes": 0,
                "zone5_target_minutes": 0,
                "cardio_sessions_target": 3,
                "strength_sessions_target": 2,
                "created_reason": "initial default",
            }
        )
        repo.create(
            {
                "effective_from_date": date(2026, 4, 13),
                "effective_to_date": None,
                "zone1_target_minutes": 0,
                "zone2_target_minutes": 175,
                "zone3_target_minutes": 0,
                "zone4_target_minutes": 0,
                "zone5_target_minutes": 0,
                "cardio_sessions_target": 3,
                "strength_sessions_target": 2,
                "created_reason": "build week",
            }
        )

        first = repo.active_for_week(date(2026, 4, 6))
        second = repo.active_for_week(date(2026, 4, 13))
        history = repo.history()

    assert first.zone2_target_minutes == 150
    assert second.zone2_target_minutes == 175
    assert [row.zone2_target_minutes for row in history] == [175, 150]


def test_sync_run_append_only_and_state_upsert():
    with SessionLocal() as db:
        repo = SyncRepository(db)
        run_a = repo.create_run(
            trigger="manual",
            resource_type="workouts",
            window_start_utc=datetime(2026, 4, 1, tzinfo=UTC),
            window_end_utc=datetime(2026, 4, 7, tzinfo=UTC),
        )
        repo.finish_run(
            run_a,
            status="success",
            inserted_count=1,
            updated_count=2,
            unchanged_count=3,
        )
        run_b = repo.create_run(trigger="scheduled", resource_type="workouts")

        state_time = datetime.now(UTC)
        repo.upsert_state(
            resource_type="workouts",
            last_successful_sync_at_utc=state_time,
            last_window_start_utc=state_time - timedelta(days=1),
            last_window_end_utc=state_time,
            cursor_text="cursor-1",
        )
        state = repo.get_state("workouts")

    assert run_a.id != run_b.id
    assert run_a.status == "success"
    assert run_b.status == "running"
    assert state.cursor_text == "cursor-1"
