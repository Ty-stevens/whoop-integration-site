import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.athlete_profile import AthleteProfile


def test_development_allows_placeholder_whoop_credentials():
    settings = Settings(app_env="development")

    assert settings.whoop_credentials_configured is False


def test_production_rejects_placeholder_secrets():
    with pytest.raises(ValidationError):
        Settings(app_env="production")


def test_production_rejects_replace_with_placeholder_secrets():
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            app_encryption_key="replace-with-a-real-secret",
            whoop_client_id="replace-with-whoop-client-id",
            whoop_client_secret="replace-with-whoop-client-secret",
        )


def test_whoop_credentials_configured_rejects_replace_with_placeholders():
    settings = Settings(
        whoop_client_id="replace-with-whoop-client-id",
        whoop_client_secret="replace-with-whoop-client-secret",
    )

    assert settings.whoop_credentials_configured is False


def test_whoop_status_does_not_expose_secrets(client):
    response = client.get("/api/v1/integrations/whoop/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "config_missing"
    assert "replace-me" not in str(payload)
    assert "WHOOP_CLIENT_SECRET" not in str(payload)


def test_athlete_profile_accepts_optional_context(client):
    response = client.put(
        "/api/v1/athlete-profile",
        json={
            "display_name": "Ty",
            "gender": "male",
            "age_years": 35,
            "height_cm": 180,
            "weight_kg": 78.5,
            "training_focus": "Triathlon base building",
            "experience_level": "intermediate",
            "notes_for_ai": "Prefers conservative deloads.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_name"] == "Ty"
    assert payload["ai_context_allowed"] is False

    persisted = client.get("/api/v1/athlete-profile")
    assert persisted.status_code == 200
    assert persisted.json()["training_focus"] == "Triathlon base building"


def test_app_settings_persist_across_requests(client):
    response = client.put(
        "/api/v1/settings",
        json={
            "auto_sync_enabled": True,
            "auto_sync_frequency": "twice_daily",
            "preferred_export_format": "csv",
            "preferred_units": "metric",
        },
    )

    assert response.status_code == 200
    persisted = client.get("/api/v1/settings")
    assert persisted.json()["auto_sync_enabled"] is True
    assert persisted.json()["auto_sync_frequency"] == "twice_daily"


def test_athlete_profile_rejects_impossible_values():
    with pytest.raises(ValidationError):
        AthleteProfile(age_years=8)

    with pytest.raises(ValidationError):
        AthleteProfile(height_cm=400)
