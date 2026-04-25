import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.time import ensure_utc
from app.schemas.whoop import WhoopStatus
from app.services.whoop.client import WhoopOAuthClient, WhoopOAuthError
from app.services.whoop.models import WhoopTokenResponse
from app.services.whoop.oauth import (
    build_authorization_url,
    consume_oauth_state,
    create_oauth_state,
)
from app.services.whoop.token_store import WhoopTokenRefreshError, WhoopTokenStore

logger = logging.getLogger("endurasync.whoop.auth")


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
        missing_refresh_token = not connection.refresh_token_encrypted
        if missing_refresh_token:
            status = "error"
        else:
            status = "expired" if expires_at <= datetime.now(UTC) else connection.status
        if status == "expired":
            message = "WHOOP access token is expired and will refresh on the next sync."
        elif status == "error" and missing_refresh_token:
            message = "WHOOP connection is missing refresh access. Reconnect WHOOP."
        elif status == "error":
            message = "WHOOP connection needs attention after a token refresh failure."
        else:
            message = "WHOOP connection is stored securely."
        logger.info(
            "whoop.auth.status status=%s credentials_configured=%s connected=%s",
            status,
            True,
            connection is not None,
        )
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
        logger.info("whoop.auth.authorization_url_created")
        return build_authorization_url(self.settings, state)

    def handle_callback(self, code: str, state: str) -> None:
        logger.info("whoop.auth.callback.start")
        consume_oauth_state(self.db, state)
        try:
            token_response = self.oauth_client.exchange_code_for_tokens(code)
            self.token_store.save_token_response(token_response)
        except (WhoopOAuthError, WhoopTokenRefreshError) as exc:
            logger.warning("whoop.auth.callback.failed error_type=%s", exc.__class__.__name__)
            raise RuntimeError("WHOOP token exchange failed") from exc
        logger.info("whoop.auth.callback.success")

    def save_mocked_tokens_for_test(self, token_response: WhoopTokenResponse) -> None:
        self.token_store.save_token_response(token_response)

    def disconnect(self) -> None:
        self.token_store.disconnect()
