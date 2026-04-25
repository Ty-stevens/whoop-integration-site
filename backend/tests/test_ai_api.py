import json
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import create_app
from app.models.facts import WorkoutModel
from app.models.overlays import GoalProfileModel
from app.schemas.goals import GoalProfileCreate
from app.services.ai.context_builder import AiContextBuilder
from app.services.ai.types import AiProviderResult
from app.services.goal_service import GoalProfileService
from tests.fact_fixtures import workout_values


class FakeBenchmarkProvider:
    def generate(self, prompt: str, *, response_format=None) -> AiProviderResult:
        assert response_format == {"type": "json_object"}
        assert "six_month_report" in prompt
        return AiProviderResult(
            text=json.dumps(
                {
                    "targets": {
                        "zone1_target_minutes": 10,
                        "zone2_target_minutes": 180,
                        "zone3_target_minutes": 20,
                        "zone4_target_minutes": 5,
                        "zone5_target_minutes": 0,
                        "cardio_sessions_target": 4,
                        "strength_sessions_target": 2,
                    },
                    "summary": "Recent training supports a modest Zone 2 increase.",
                    "confidence": "medium",
                    "changes": [
                        {
                            "metric": "zone2_target_minutes",
                            "current_value": 150,
                            "recommended_value": 180,
                            "reason": "Six-month report shows consistent aerobic volume.",
                            "sources": [
                                {
                                    "source_type": "six_month_report",
                                    "date": "2026-04",
                                    "metric": "zone2_minutes",
                                    "value": 160,
                                }
                            ],
                        }
                    ],
                }
            )
        )


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


def test_ai_benchmark_update_disabled_does_not_mutate_goals(client):
    response = client.post("/api/v1/ai/benchmark-update", json={"apply": True})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "disabled"
    with SessionLocal() as db:
        assert db.query(GoalProfileModel).count() == 0


def test_ai_status_reports_setup_error_without_breaking_app(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "openai_compatible")
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())

    ai_response = client.get("/api/v1/ai/status")
    health_response = client.get("/api/v1/health")

    assert ai_response.status_code == 200
    assert ai_response.json()["status"] == "failing"
    assert "MODEL" in ai_response.json()["message"]
    assert health_response.status_code == 200


def test_ai_benchmark_preview_is_structured_and_does_not_apply(monkeypatch):
    _enable_ai(monkeypatch)
    monkeypatch.setattr(
        "app.services.ai.benchmark_service.provider_from_settings",
        lambda settings: FakeBenchmarkProvider(),
    )
    client = TestClient(create_app())
    with SessionLocal() as db:
        GoalProfileService(db).create_profile(_base_goal_payload())

    response = client.post("/api/v1/ai/benchmark-update", json={"apply": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["applied"] is False
    assert payload["proposal"]["targets"]["zone2_target_minutes"] == 180
    with SessionLocal() as db:
        assert db.query(GoalProfileModel).count() == 1


def test_ai_benchmark_apply_creates_goal_with_provenance(monkeypatch):
    _enable_ai(monkeypatch)
    monkeypatch.setattr(
        "app.services.ai.benchmark_service.provider_from_settings",
        lambda settings: FakeBenchmarkProvider(),
    )
    client = TestClient(create_app())
    effective_date = _next_monday(date.today())
    with SessionLocal() as db:
        GoalProfileService(db).create_profile(_base_goal_payload())

    response = client.post(
        "/api/v1/ai/benchmark-update",
        json={"apply": True, "effective_from_date": effective_date.isoformat()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["applied"] is True
    assert payload["profile"]["created_source"] == "ai_benchmark_update"
    with SessionLocal() as db:
        profile = (
            db.query(GoalProfileModel)
            .order_by(GoalProfileModel.effective_from_date.desc())
            .first()
        )
        assert profile is not None
        assert profile.zone2_target_minutes == 180
        assert profile.ai_provenance_json["confidence"] == "medium"
        assert profile.ai_provenance_json["changes"][0]["metric"] == "zone2_target_minutes"


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


def _enable_ai(monkeypatch) -> None:
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "openai_compatible")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()


def _base_goal_payload() -> GoalProfileCreate:
    return GoalProfileCreate(
        effective_from_date=_current_monday(date.today()),
        zone1_target_minutes=0,
        zone2_target_minutes=150,
        zone3_target_minutes=0,
        zone4_target_minutes=0,
        zone5_target_minutes=0,
        cardio_sessions_target=3,
        strength_sessions_target=2,
    )


def _current_monday(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _next_monday(value: date) -> date:
    days_until_monday = (7 - value.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return value + timedelta(days=days_until_monday)
