from datetime import UTC, date, datetime

from sqlalchemy import text

from app.db.session import SessionLocal
from app.jobs import check_integrity
from app.models import GoalProfileModel, RecoveryModel, SleepModel, SyncStateModel, WorkoutModel


def _workout(**overrides):
    values = {
        "external_id": "workout-1",
        "whoop_user_id": "whoop-user-1",
        "external_created_at_utc": datetime(2026, 4, 1, 10, tzinfo=UTC),
        "external_updated_at_utc": datetime(2026, 4, 1, 11, tzinfo=UTC),
        "start_time_utc": datetime(2026, 4, 6, 7, tzinfo=UTC),
        "end_time_utc": datetime(2026, 4, 6, 8, tzinfo=UTC),
        "timezone_offset_text": "+00:00",
        "local_start_date": date(2026, 4, 6),
        "iso_week_start_date": date(2026, 4, 6),
        "local_month_start_date": date(2026, 4, 1),
        "sport_name": "Running",
        "score_state": "SCORED",
        "classification": "cardio",
        "duration_seconds": 3600,
        "strain": 10.5,
        "average_hr": 142,
        "max_hr": 171,
        "percent_recorded": 99.0,
        "zone0_seconds": 100,
        "zone1_seconds": 500,
        "zone2_seconds": 2000,
        "zone3_seconds": 700,
        "zone4_seconds": 250,
        "zone5_seconds": 50,
        "raw_payload_json": {"id": "workout-1"},
        "payload_hash": "hash-1",
        "source_revision": 1,
        "imported_at_utc": datetime(2026, 4, 6, 9, tzinfo=UTC),
    }
    values.update(overrides)
    return WorkoutModel(**values)


def _sleep(**overrides):
    values = {
        "external_id": "sleep-1",
        "cycle_id": "cycle-1",
        "whoop_user_id": "whoop-user-1",
        "external_created_at_utc": datetime(2026, 4, 6, 6, tzinfo=UTC),
        "external_updated_at_utc": datetime(2026, 4, 6, 7, tzinfo=UTC),
        "start_time_utc": datetime(2026, 4, 5, 22, tzinfo=UTC),
        "end_time_utc": datetime(2026, 4, 6, 6, tzinfo=UTC),
        "timezone_offset_text": "+00:00",
        "local_start_date": date(2026, 4, 5),
        "iso_week_start_date": date(2026, 3, 30),
        "local_month_start_date": date(2026, 4, 1),
        "nap": False,
        "score_state": "SCORED",
        "sleep_duration_seconds": 28800,
        "sleep_performance": 91.0,
        "sleep_efficiency": 88.0,
        "raw_payload_json": {"id": "sleep-1"},
        "payload_hash": "sleep-hash-1",
        "source_revision": 1,
        "imported_at_utc": datetime(2026, 4, 6, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return SleepModel(**values)


def _goal(**overrides):
    values = {
        "effective_from_date": date(2026, 4, 6),
        "effective_to_date": None,
        "zone1_target_minutes": 0,
        "zone2_target_minutes": 150,
        "zone3_target_minutes": 0,
        "zone4_target_minutes": 0,
        "zone5_target_minutes": 0,
        "cardio_sessions_target": 3,
        "strength_sessions_target": 2,
        "created_reason": "test",
    }
    values.update(overrides)
    return GoalProfileModel(**values)


def test_check_integrity_reports_data_problems(capsys):
    with SessionLocal() as db:
        db.add_all(
            [
                _goal(effective_to_date=date(2026, 4, 12)),
                _goal(effective_from_date=date(2026, 4, 10), zone2_target_minutes=175),
                _workout(
                    external_id="workout-bad-durations",
                    start_time_utc=datetime(2026, 4, 6, 8, tzinfo=UTC),
                    end_time_utc=datetime(2026, 4, 6, 7, tzinfo=UTC),
                    duration_seconds=1800,
                    zone0_seconds=0,
                    zone1_seconds=0,
                    zone2_seconds=0,
                    zone3_seconds=0,
                    zone4_seconds=0,
                    zone5_seconds=0,
                ),
                _workout(
                    external_id="workout-bad-zones",
                    zone0_seconds=1000,
                    zone1_seconds=1000,
                    zone2_seconds=1000,
                    zone3_seconds=1000,
                    zone4_seconds=1000,
                    zone5_seconds=1000,
                ),
                _sleep(
                    external_id="sleep-bad-durations",
                    start_time_utc=datetime(2026, 4, 6, 6, tzinfo=UTC),
                    end_time_utc=datetime(2026, 4, 6, 5, tzinfo=UTC),
                    sleep_duration_seconds=3600,
                ),
                RecoveryModel(
                    cycle_id="cycle-1",
                    whoop_user_id="whoop-user-1",
                    local_date=date(2026, 4, 6),
                    iso_week_start_date=date(2026, 4, 6),
                    local_month_start_date=date(2026, 4, 1),
                    score_state="SCORED",
                    recovery_score=72.0,
                    hrv_ms=61.5,
                    resting_hr=48,
                    respiratory_rate=14.2,
                    skin_temp_celsius=36.4,
                    spo2_percent=98.0,
                    raw_payload_json={"cycle_id": "cycle-1"},
                    payload_hash="recovery-hash-1",
                    source_revision=1,
                    imported_at_utc=datetime(2026, 4, 6, 8, tzinfo=UTC),
                ),
            ]
        )
        db.flush()
        db.commit()
        db.connection().exec_driver_sql("PRAGMA foreign_keys=OFF")
        db.execute(
            text(
                "INSERT INTO workout_annotations "
                "(workout_id, manual_classification, manual_strength_split, tag, notes, "
                "created_at_utc, updated_at_utc) "
                "VALUES (:workout_id, :manual_classification, :manual_strength_split, "
                ":tag, :notes, :created_at_utc, :updated_at_utc)"
            ),
            {
                "workout_id": 999999,
                "manual_classification": "strength",
                "manual_strength_split": None,
                "tag": "manual-review",
                "notes": "orphan",
                "created_at_utc": datetime(2026, 4, 6, 9, tzinfo=UTC),
                "updated_at_utc": datetime(2026, 4, 6, 9, tzinfo=UTC),
            },
        )
        db.commit()

    exit_code = check_integrity.main([])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "overlap between goal profile" in output
    assert "workout-bad-durations" in output
    assert "zone_total_seconds" in output
    assert "annotation" in output
    assert "missing sync_state row for workouts" in output
    assert "missing sync_state row for sleeps" in output
    assert "missing sync_state row for recoveries" in output


def test_check_integrity_is_clean_when_expected_rows_exist(capsys):
    with SessionLocal() as db:
        db.add_all(
            [
                _goal(),
                _workout(external_id="workout-clean"),
                _sleep(external_id="sleep-clean"),
                RecoveryModel(
                    cycle_id="cycle-clean",
                    whoop_user_id="whoop-user-1",
                    local_date=date(2026, 4, 6),
                    iso_week_start_date=date(2026, 4, 6),
                    local_month_start_date=date(2026, 4, 1),
                    score_state="SCORED",
                    recovery_score=72.0,
                    hrv_ms=61.5,
                    resting_hr=48,
                    respiratory_rate=14.2,
                    skin_temp_celsius=36.4,
                    spo2_percent=98.0,
                    raw_payload_json={"cycle_id": "cycle-clean"},
                    payload_hash="recovery-hash-clean",
                    source_revision=1,
                    imported_at_utc=datetime(2026, 4, 6, 8, tzinfo=UTC),
                ),
                SyncStateModel(resource_type="workouts"),
                SyncStateModel(resource_type="sleeps"),
                SyncStateModel(resource_type="recoveries"),
            ]
        )
        db.commit()

    exit_code = check_integrity.main([])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Integrity check clean." in output
