import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.db.session import normalize_database_url
from app.main import create_app
from app.schemas.athlete_profile import AthleteProfile


def test_development_allows_placeholder_whoop_credentials():
    settings = Settings(app_env="development")

    assert settings.whoop_credentials_configured is False


def test_production_allows_placeholder_secrets_for_graceful_degradation(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("APP_BASE_URL", "https://app.example.com")
    monkeypatch.setenv(
        "WHOOP_REDIRECT_URI", "https://app.example.com/api/v1/integrations/whoop/callback"
    )
    monkeypatch.setenv("TRUSTED_HOSTS", "app.example.com")

    settings = Settings(
        _env_file=None,
    )

    assert settings.api_auth_enabled is False
    assert settings.whoop_credentials_configured is False


def test_production_rejects_insecure_public_urls(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "http://app.example.com")
    monkeypatch.setenv("APP_BASE_URL", "http://app.example.com")
    monkeypatch.setenv(
        "WHOOP_REDIRECT_URI", "http://app.example.com/api/v1/integrations/whoop/callback"
    )
    monkeypatch.setenv("TRUSTED_HOSTS", "app.example.com")

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
        )


def test_whoop_credentials_configured_rejects_replace_with_placeholders():
    settings = Settings(
        whoop_client_id="replace-with-whoop-client-id",
        whoop_client_secret="replace-with-whoop-client-secret",
    )

    assert settings.whoop_credentials_configured is False


def test_vercel_sqlite_database_is_reported_as_ephemeral(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    settings = Settings(database_url="sqlite:///./data/endurasync.db")

    assert settings.database_storage_status == "ephemeral"
    assert "durable DATABASE_URL" in settings.database_storage_message


def test_postgres_database_url_is_normalized_for_psycopg():
    assert (
        normalize_database_url("postgres://user:pass@example.com/db?sslmode=require")
        == "postgresql+psycopg://user:pass@example.com/db?sslmode=require"
    )
    assert (
        normalize_database_url("postgresql://user:pass@example.com/db")
        == "postgresql+psycopg://user:pass@example.com/db"
    )


def test_vercel_sqlite_blocks_whoop_connect_with_actionable_message(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("WHOOP_CLIENT_ID", "client-id")
    monkeypatch.setenv("WHOOP_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("APP_ENCRYPTION_KEY", "test-encryption-key")
    get_settings.cache_clear()
    test_client = TestClient(create_app())

    status = test_client.get("/api/v1/integrations/whoop/status")
    connect = test_client.get("/api/v1/integrations/whoop/connect/start")

    assert status.status_code == 200
    assert status.json()["status"] == "storage_misconfigured"
    assert connect.status_code == 503
    assert "durable DATABASE_URL" in connect.json()["detail"]


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
