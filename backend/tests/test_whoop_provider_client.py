from datetime import UTC, datetime
from urllib.parse import parse_qs

import httpx
import pytest

from app.core.config import Settings
from app.core.security import decrypt_secret
from app.db.session import SessionLocal
from app.models.whoop_connection import WhoopConnectionModel
from app.services.whoop.auth_service import WhoopAuthService
from app.services.whoop.client import WhoopOAuthClient
from app.services.whoop.models import WhoopTokenResponse
from app.services.whoop.provider_client import WhoopProviderClient, WhoopProviderError
from app.services.whoop.token_store import WhoopTokenStore


def configured_settings() -> Settings:
    return Settings(
        app_env="test",
        app_encryption_key="test-encryption-key",
        whoop_client_id="client-id",
        whoop_client_secret="client-secret",
        whoop_redirect_uri="http://localhost:8000/api/v1/integrations/whoop/callback",
        whoop_token_url="https://whoop.example/token",
        whoop_api_base_url="https://whoop.example/developer",
    )


def provider_client(
    db,
    settings: Settings,
    http_client: httpx.Client,
) -> WhoopProviderClient:
    token_store = WhoopTokenStore(db, settings)
    oauth_client = WhoopOAuthClient(settings=settings, http_client=http_client)
    return WhoopProviderClient(
        settings=settings,
        token_store=token_store,
        oauth_client=oauth_client,
        http_client=http_client,
        retry_delay_seconds=0,
    )


def save_tokens(
    db,
    settings: Settings,
    *,
    access_token: str = "access-token",
    refresh_token: str = "refresh-token",
    expires_in: int = 3600,
) -> None:
    WhoopTokenStore(db, settings).save_token_response(
        WhoopTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scope="read:workout read:sleep read:recovery",
            whoop_user_id="whoop-user-1",
        )
    )


def token_json(
    *,
    access_token: str = "new-access-token",
    refresh_token: str = "new-refresh-token",
    expires_in: int = 3600,
) -> dict:
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "scope": "read:workout read:sleep read:recovery",
    }


def empty_collection(next_token: str | None = None) -> dict:
    return {"records": [], "next_token": next_token}


def test_refresh_request_uses_refresh_grant_and_stores_encrypted_tokens():
    settings = configured_settings()
    refresh_body: dict[str, list[str]] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal refresh_body
        assert request.url == settings.whoop_token_url
        refresh_body = parse_qs(request.content.decode("utf-8"))
        return httpx.Response(200, json=token_json())

    with SessionLocal() as db:
        save_tokens(
            db,
            settings,
            access_token="old-access",
            refresh_token="old-refresh",
            expires_in=1,
        )
        client = httpx.Client(transport=httpx.MockTransport(handler))
        tokens = WhoopTokenStore(db, settings).refresh_now(
            WhoopOAuthClient(settings=settings, http_client=client)
        )
        row = db.get(WhoopConnectionModel, 1)

    assert refresh_body["grant_type"] == ["refresh_token"]
    assert refresh_body["refresh_token"] == ["old-refresh"]
    assert refresh_body["client_id"] == ["client-id"]
    assert refresh_body["client_secret"] == ["client-secret"]
    assert tokens is not None
    assert tokens.access_token == "new-access-token"
    assert row is not None
    assert row.last_token_refresh_at_utc is not None
    assert row.access_token_encrypted != "new-access-token"
    assert row.refresh_token_encrypted != "new-refresh-token"
    decrypted_access_token = decrypt_secret(row.access_token_encrypted, settings.app_encryption_key)
    assert decrypted_access_token == "new-access-token"


def test_nearly_expired_token_refreshes_before_provider_request():
    settings = configured_settings()
    refresh_count = 0
    provider_auth_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal refresh_count
        if request.url == settings.whoop_token_url:
            refresh_count += 1
            return httpx.Response(200, json=token_json(access_token="fresh-access"))

        provider_auth_headers.append(request.headers.get("authorization"))
        return httpx.Response(200, json=empty_collection())

    with SessionLocal() as db:
        save_tokens(db, settings, access_token="stale-access", expires_in=60)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        pages = provider_client(db, settings, client).fetch_workouts()
        row = db.get(WhoopConnectionModel, 1)

    assert refresh_count == 1
    assert provider_auth_headers == ["Bearer fresh-access"]
    assert len(pages) == 1
    assert row is not None
    assert row.last_token_refresh_at_utc is not None


def test_collection_methods_use_base_url_paths_query_params_and_bearer_token():
    settings = configured_settings()
    seen_paths: list[str] = []
    seen_params: list[dict[str, str]] = []
    seen_headers: list[str | None] = []
    start = datetime(2026, 4, 1, tzinfo=UTC)
    end = datetime(2026, 4, 2, tzinfo=UTC)

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        seen_params.append(dict(request.url.params))
        seen_headers.append(request.headers.get("authorization"))
        return httpx.Response(200, json=empty_collection())

    with SessionLocal() as db:
        save_tokens(db, settings)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        whoop = provider_client(db, settings, client)
        whoop.fetch_workouts(start=start, end=end, limit=25)
        whoop.fetch_sleeps(start=start, end=end, limit=25)
        whoop.fetch_recoveries(start=start, end=end, limit=25)

    assert seen_paths == [
        "/developer/v2/activity/workout",
        "/developer/v2/activity/sleep",
        "/developer/v2/recovery",
    ]
    assert seen_headers == ["Bearer access-token", "Bearer access-token", "Bearer access-token"]
    assert all(params["limit"] == "25" for params in seen_params)
    assert all(params["start"].startswith("2026-04-01T00:00:00") for params in seen_params)
    assert all(params["end"].startswith("2026-04-02T00:00:00") for params in seen_params)


def test_pagination_follows_next_token_until_exhausted():
    settings = configured_settings()
    next_tokens_seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        next_token = request.url.params.get("nextToken")
        next_tokens_seen.append(next_token)
        if next_token is None:
            return httpx.Response(200, json=empty_collection(next_token="page-2"))
        return httpx.Response(200, json=empty_collection())

    with SessionLocal() as db:
        save_tokens(db, settings)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        pages = provider_client(db, settings, client).fetch_workouts()

    assert next_tokens_seen == [None, "page-2"]
    assert len(pages) == 2


def test_repeated_pagination_token_raises_provider_error():
    settings = configured_settings()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=empty_collection(next_token="same-token"))

    with SessionLocal() as db:
        save_tokens(db, settings)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        with pytest.raises(WhoopProviderError, match="repeated next token"):
            provider_client(db, settings, client).fetch_workouts()


def test_collection_limit_must_stay_within_whoop_documented_bounds():
    settings = configured_settings()

    with SessionLocal() as db:
        save_tokens(db, settings)
        client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
        with pytest.raises(WhoopProviderError, match="limit must be between 1 and 25"):
            provider_client(db, settings, client).fetch_workouts(limit=26)


def test_malformed_json_response_raises_provider_error():
    settings = configured_settings()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    with SessionLocal() as db:
        save_tokens(db, settings)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        with pytest.raises(WhoopProviderError, match="not valid JSON"):
            provider_client(db, settings, client).fetch_workouts()


def test_unauthorized_response_refreshes_once_and_retries_original_request():
    settings = configured_settings()
    refresh_count = 0
    provider_auth_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal refresh_count
        if request.url == settings.whoop_token_url:
            refresh_count += 1
            return httpx.Response(200, json=token_json(access_token="retry-access"))

        provider_auth_headers.append(request.headers.get("authorization"))
        if request.headers.get("authorization") == "Bearer old-access":
            return httpx.Response(401, json={"error": "invalid_token"})
        return httpx.Response(200, json=empty_collection())

    with SessionLocal() as db:
        save_tokens(db, settings, access_token="old-access", refresh_token="refresh-token")
        client = httpx.Client(transport=httpx.MockTransport(handler))
        pages = provider_client(db, settings, client).fetch_workouts()

    assert refresh_count == 1
    assert provider_auth_headers == ["Bearer old-access", "Bearer retry-access"]
    assert len(pages) == 1


def test_transient_provider_errors_retry_with_bounded_attempts():
    settings = configured_settings()
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        if request_count < 3:
            return httpx.Response(500, json={"error": "temporary"})
        return httpx.Response(200, json=empty_collection())

    with SessionLocal() as db:
        save_tokens(db, settings)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        pages = provider_client(db, settings, client).fetch_workouts()

    assert request_count == 3
    assert len(pages) == 1


def test_persistent_transient_provider_errors_raise_provider_error():
    settings = configured_settings()
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(429, json={"error": "rate_limit"})

    with SessionLocal() as db:
        save_tokens(db, settings)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        with pytest.raises(WhoopProviderError, match="429"):
            provider_client(db, settings, client).fetch_workouts()

    assert request_count == 3


def test_refresh_failure_marks_connection_error():
    settings = configured_settings()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == settings.whoop_token_url
        return httpx.Response(500, json={"error": "refresh_failed"})

    with SessionLocal() as db:
        save_tokens(db, settings, access_token="stale-access", expires_in=60)
        client = httpx.Client(transport=httpx.MockTransport(handler))
        with pytest.raises(WhoopProviderError, match="token refresh failed"):
            provider_client(db, settings, client).fetch_workouts()
        row = db.get(WhoopConnectionModel, 1)
        status = WhoopAuthService(db, settings=settings).status()

    assert row is not None
    assert row.status == "error"
    assert status.status == "error"
    assert "refresh failure" in status.message


def test_missing_connection_raises_provider_error():
    settings = configured_settings()

    with SessionLocal() as db:
        client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
        with pytest.raises(WhoopProviderError, match="connection is not available"):
            provider_client(db, settings, client).fetch_workouts()
