from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_protected_route_requires_api_key_when_configured(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("API_AUTH_TOKEN", "dev-secret-token")
    get_settings.cache_clear()
    client = TestClient(create_app())

    unauthorized = client.get("/api/v1/settings")
    authorized = client.get("/api/v1/settings", headers={"X-API-Key": "dev-secret-token"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_health_route_remains_public_when_api_key_is_configured(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("API_AUTH_TOKEN", "dev-secret-token")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
