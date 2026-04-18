from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.security import decrypt_secret, encrypt_secret
from app.db.session import SessionLocal
from app.main import create_app
from app.models.whoop_connection import WhoopConnectionModel
from app.services.whoop.auth_service import WhoopAuthService
from app.services.whoop.client import WhoopOAuthClient
from app.services.whoop.models import WhoopTokenResponse
from app.services.whoop.oauth import create_oauth_state


def configured_settings() -> Settings:
    return Settings(
        app_env="test",
        app_encryption_key="test-encryption-key",
        whoop_client_id="client-id",
        whoop_client_secret="client-secret",
        whoop_redirect_uri="http://localhost:8000/api/v1/integrations/whoop/callback",
        whoop_token_url="https://whoop.example/token",
    )


def test_secret_encryption_round_trip():
    encrypted = encrypt_secret("access-token", "local-key")

    assert encrypted != "access-token"
    assert decrypt_secret(encrypted, "local-key") == "access-token"


def test_connect_builds_authorization_url_without_secret(monkeypatch):
    monkeypatch.setenv("WHOOP_CLIENT_ID", "client-id")
    monkeypatch.setenv("WHOOP_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("APP_ENCRYPTION_KEY", "test-encryption-key")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/v1/integrations/whoop/connect", follow_redirects=False)

    assert response.status_code in {307, 308}
    location = response.headers["location"]
    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    assert params["client_id"] == ["client-id"]
    assert "state" in params
    assert "client-secret" not in location


def test_callback_rejects_missing_or_invalid_state(client):
    missing = client.get("/api/v1/integrations/whoop/callback?code=abc")
    invalid = client.get("/api/v1/integrations/whoop/callback?code=abc&state=not-real")

    assert missing.status_code == 400
    assert invalid.status_code == 400


def test_token_store_never_persists_plaintext_tokens():
    settings = configured_settings()
    with SessionLocal() as db:
        WhoopAuthService(db, settings=settings).save_mocked_tokens_for_test(
            WhoopTokenResponse(
                access_token="plain-access",
                refresh_token="plain-refresh",
                expires_in=3600,
                scope="read:workout",
                whoop_user_id="whoop-user-1",
            )
        )
        row = db.get(WhoopConnectionModel, 1)

    assert row is not None
    assert row.access_token_encrypted != "plain-access"
    assert row.refresh_token_encrypted != "plain-refresh"
    assert decrypt_secret(row.access_token_encrypted, settings.app_encryption_key) == "plain-access"


def test_callback_exchanges_code_and_stores_encrypted_tokens():
    settings = configured_settings()

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode("utf-8")
        assert "client_secret=client-secret" in body
        return httpx.Response(
            200,
            json={
                "access_token": "callback-access",
                "refresh_token": "callback-refresh",
                "expires_in": 1800,
                "scope": "read:profile read:workout",
            },
        )

    with SessionLocal() as db:
        state = create_oauth_state(db)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        oauth_client = WhoopOAuthClient(settings=settings, http_client=client)
        WhoopAuthService(db, settings=settings, oauth_client=oauth_client).handle_callback(
            code="code-from-whoop",
            state=state,
        )
        row = db.get(WhoopConnectionModel, 1)

    assert row is not None
    assert row.status == "connected"
    assert row.access_token_encrypted != "callback-access"


def test_status_reports_expired_connection():
    settings = configured_settings()
    with SessionLocal() as db:
        service = WhoopAuthService(db, settings=settings)
        service.save_mocked_tokens_for_test(
            WhoopTokenResponse(
                access_token="access",
                refresh_token="refresh",
                expires_in=3600,
            )
        )
        row = service.token_store.get_connection()
        assert row is not None
        row.token_expires_at_utc = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()

        status = service.status()

    assert status.status == "expired"
