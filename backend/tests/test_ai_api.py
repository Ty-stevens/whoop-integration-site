from app.db.session import SessionLocal
from app.models.facts import WorkoutModel
from app.services.ai.context_builder import AiContextBuilder
from tests.fact_fixtures import workout_values


def test_ai_status_disabled_by_default(client):
    response = client.get("/api/v1/ai/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "disabled"
    assert payload["enabled"] is False


def test_ai_weekly_summary_disabled_is_calm(client):
    response = client.post("/api/v1/ai/weekly-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "disabled"
    assert "disabled" in payload["message"].lower()


def test_ai_goal_suggestions_disabled_does_not_mutate_goals(client):
    response = client.post("/api/v1/ai/goal-suggestions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "disabled"
    assert payload["suggestions"] == []


def test_ai_context_excludes_raw_payloads_and_tokens():
    with SessionLocal() as db:
        row = WorkoutModel(
            **workout_values(raw_payload_json={"id": "workout-1", "access_token": "secret"})
        )
        db.add(row)
        db.commit()
        context = AiContextBuilder(db).build()

    body = str(context)
    assert "raw_payload_json" not in body
    assert "access_token" not in body
    assert "refresh_token" not in body
    assert "secret" not in body
