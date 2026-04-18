from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.time import ensure_utc
from app.schemas.whoop import WhoopStatus
from app.services.whoop.client import WhoopOAuthClient
from app.services.whoop.models import WhoopTokenResponse
from app.services.whoop.oauth import (
    build_authorization_url,
    consume_oauth_state,
    create_oauth_state,
)
from app.services.whoop.token_store import WhoopTokenStore


class WhoopAuthService:
    def __init__(
        self,
        db: Session,
        settings: Settings | None = None,
        oauth_client: WhoopOAuthClient | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.token_store = WhoopTokenStore(db, self.settings)
        self.oauth_client = oauth_client or WhoopOAuthClient(self.settings)

    def status(self) -> WhoopStatus:
        if not self.settings.whoop_credentials_configured:
            return WhoopStatus(
                status="config_missing",
                credentials_configured=False,
                message="WHOOP credentials are not configured. Local boot does not require them.",
            )

        connection = self.token_store.get_connection()
        if connection is None:
            return WhoopStatus(
                status="disconnected",
                credentials_configured=True,
                message="WHOOP credentials are configured, but no connection is stored.",
            )

        expires_at = ensure_utc(connection.token_expires_at_utc)
        status = "expired" if expires_at <= datetime.now(UTC) else connection.status
        if status == "expired":
            message = "WHOOP connection token has expired."
        elif status == "error":
            message = "WHOOP connection needs attention after a token refresh failure."
        else:
            message = "WHOOP connection is stored securely."
        return WhoopStatus(
            status=status,  # type: ignore[arg-type]
            credentials_configured=True,
            connected_at_utc=connection.connected_at_utc,
            last_token_refresh_at_utc=connection.last_token_refresh_at_utc,
            token_expires_at_utc=connection.token_expires_at_utc,
            granted_scopes=connection.granted_scopes,
            message=message,
        )

    def authorization_url(self) -> str | None:
        if not self.settings.whoop_credentials_configured:
            return None
        state = create_oauth_state(self.db)
        return build_authorization_url(self.settings, state)

    def handle_callback(self, code: str, state: str) -> None:
        consume_oauth_state(self.db, state)
        try:
            token_response = self.oauth_client.exchange_code_for_tokens(code)
        except httpx.HTTPError as exc:
            raise RuntimeError("WHOOP token exchange failed") from exc
        self.token_store.save_token_response(token_response)

    def save_mocked_tokens_for_test(self, token_response: WhoopTokenResponse) -> None:
        self.token_store.save_token_response(token_response)

    def disconnect(self) -> None:
        self.token_store.disconnect()
