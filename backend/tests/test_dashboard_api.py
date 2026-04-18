from datetime import UTC, date, datetime

from app.db.session import SessionLocal
from app.models.facts import RecoveryModel, WorkoutModel
from app.repositories.sync import SyncRepository
from app.services.goal_service import seed_default_goals
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


def test_current_week_without_query_returns_summary(client):
    response = client.get("/api/v1/dashboard/current-week")

    assert response.status_code == 200
    payload = response.json()
    assert "week_start_date" in payload
    assert "week_end_date" in payload
    assert len(payload["zones"]) == 5
    assert payload["total_training_seconds"] == 0


def test_current_week_explicit_monday_returns_empty_no_goal_state(client):
    response = client.get("/api/v1/dashboard/current-week?week_start_date=2026-04-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["week_start_date"] == "2026-04-06"
    assert payload["week_end_date"] == "2026-04-12"
    assert payload["has_goal_profile"] is False
    assert payload["zones"][1]["zone"] == 2
    assert payload["zones"][1]["target_minutes"] == 0
    assert payload["zones"][1]["percent_complete"] is None


def test_current_week_non_monday_returns_422(client):
    response = client.get("/api/v1/dashboard/current-week?week_start_date=2026-04-07")

    assert response.status_code == 422
    assert "Monday ISO week start" in response.text


def test_current_week_seeded_goal_returns_targets(client):
    with SessionLocal() as db:
        seed_default_goals(db, effective_from_date=date(2026, 4, 6))

    response = client.get("/api/v1/dashboard/current-week?week_start_date=2026-04-06")

    assert response.status_code == 200
    payload = response.json()
    zone2 = next(item for item in payload["zones"] if item["zone"] == 2)
    assert payload["has_goal_profile"] is True
    assert zone2["target_minutes"] == 150
    assert zone2["remaining_minutes"] == 150
    assert payload["cardio_sessions"]["target"] == 3
    assert payload["strength_sessions"]["target"] == 2


def test_current_week_populated_week_returns_dashboard_metrics(client):
    sync_time = datetime(2026, 4, 14, 12, tzinfo=UTC)
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
        SyncRepository(db).upsert_state(
            resource_type="workouts",
            last_successful_sync_at_utc=sync_time,
            last_window_start_utc=sync_time,
            last_window_end_utc=sync_time,
        )

    response = client.get("/api/v1/dashboard/current-week?week_start_date=2026-04-06")

    assert response.status_code == 200
    payload = response.json()
    zone2 = next(item for item in payload["zones"] if item["zone"] == 2)
    assert zone2["actual_seconds"] == 4000
    assert payload["cardio_sessions"]["completed"] == 1
    assert payload["strength_sessions"]["completed"] == 1
    assert payload["total_training_seconds"] == 7200
    assert payload["average_recovery_score"] == 76
    assert payload["average_daily_strain"] == 8
    assert payload["last_successful_sync_at_utc"].startswith("2026-04-14T12:00:00")


def test_current_week_response_does_not_expose_raw_payloads_or_secrets(client):
    with SessionLocal() as db:
        seed_default_goals(db, effective_from_date=date(2026, 4, 6))
        create_workout(
            db,
            raw_payload_json={"id": "workout-1", "access_token": "secret"},
        )

    response = client.get("/api/v1/dashboard/current-week?week_start_date=2026-04-06")

    assert response.status_code == 200
    body = response.text
    assert "raw_payload_json" not in body
    assert "access_token" not in body
    assert "refresh_token" not in body
    assert "secret" not in body
    assert "client-secret" not in body
