from datetime import date

from app.db.session import SessionLocal
from app.services.goal_service import seed_default_goals


def test_active_goal_returns_empty_state_when_none_exists(client):
    response = client.get("/api/v1/goals/active")

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"] is None
    assert "No active goal profile" in payload["message"]


def test_create_goal_profile_and_resolve_active_for_week(client):
    create_response = client.post(
        "/api/v1/goals/",
        json={
            "effective_from_date": "2026-04-06",
            "zone1_target_minutes": 0,
            "zone2_target_minutes": 150,
            "zone3_target_minutes": 0,
            "zone4_target_minutes": 0,
            "zone5_target_minutes": 0,
            "cardio_sessions_target": 3,
            "strength_sessions_target": 2,
            "created_reason": "api test",
        },
    )

    week_response = client.get("/api/v1/goals/for-week?week_start_date=2026-04-06")

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["id"] == 1
    assert created["zone2_target_minutes"] == 150
    assert week_response.status_code == 200
    assert week_response.json()["profile"]["id"] == 1


def test_goal_history_returns_newest_first(client):
    with SessionLocal() as db:
        seed_default_goals(db, effective_from_date=date(2026, 4, 6))

    client.post(
        "/api/v1/goals/",
        json={
            "effective_from_date": "2026-04-13",
            "zone2_target_minutes": 175,
            "cardio_sessions_target": 3,
            "strength_sessions_target": 2,
            "created_reason": "build week",
        },
    )

    response = client.get("/api/v1/goals/history")

    assert response.status_code == 200
    profiles = response.json()["profiles"]
    assert [profile["zone2_target_minutes"] for profile in profiles] == [175, 150]


def test_invalid_goal_dates_and_negative_targets_return_validation_errors(client):
    non_monday = client.post(
        "/api/v1/goals/",
        json={"effective_from_date": "2026-04-07", "zone2_target_minutes": 150},
    )
    negative = client.post(
        "/api/v1/goals/",
        json={"effective_from_date": "2026-04-06", "zone2_target_minutes": -1},
    )
    bad_week_lookup = client.get("/api/v1/goals/for-week?week_start_date=2026-04-07")

    assert non_monday.status_code == 422
    assert negative.status_code == 422
    assert bad_week_lookup.status_code == 422


def test_goal_api_responses_do_not_expose_secrets_or_raw_payloads(client):
    client.post(
        "/api/v1/goals/",
        json={
            "effective_from_date": "2026-04-06",
            "zone2_target_minutes": 150,
            "cardio_sessions_target": 3,
            "strength_sessions_target": 2,
            "created_reason": "safe response test",
        },
    )

    response = client.get("/api/v1/goals/history")

    body = response.text
    assert "access_token" not in body
    assert "refresh_token" not in body
    assert "raw_payload_json" not in body
    assert "AI_API_KEY" not in body
