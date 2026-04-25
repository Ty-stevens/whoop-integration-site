import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import decrypt_secret, encrypt_secret
from app.core.time import ensure_utc
from app.models.whoop_connection import WhoopConnectionModel
from app.services.whoop.models import StoredWhoopTokens, WhoopTokenResponse

logger = logging.getLogger("endurasync.whoop.tokens")


class WhoopTokenRefreshError(RuntimeError):
    pass


class WhoopTokenStore:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def get_connection(self) -> WhoopConnectionModel | None:
        return self.db.scalar(select(WhoopConnectionModel).order_by(WhoopConnectionModel.id.asc()))

    def save_token_response(
        self,
        token_response: WhoopTokenResponse,
        *,
        refreshed: bool = False,
    ) -> WhoopConnectionModel:
        now = datetime.now(UTC)
        connection = self.get_connection()
        if connection is None:
            connection = WhoopConnectionModel()
            existing_refresh_token_encrypted = None
            is_new_connection = True
        else:
            existing_refresh_token_encrypted = connection.refresh_token_encrypted
            is_new_connection = False

        if token_response.refresh_token is None:
            if refreshed and existing_refresh_token_encrypted:
                refresh_token_encrypted = existing_refresh_token_encrypted
                logger.info("whoop.tokens.refresh_token_reused")
            else:
                if is_new_connection:
                    self.db.rollback()
                else:
                    connection.status = "error"
                    connection.updated_at_utc = now
                    self.db.commit()
                logger.warning("whoop.tokens.missing_refresh_token refreshed=%s", refreshed)
                raise WhoopTokenRefreshError(
                    "WHOOP token response did not include a refresh token; reconnect WHOOP"
                )
        else:
            refresh_token_encrypted = encrypt_secret(
                token_response.refresh_token,
                self.settings.app_encryption_key,
            )

        if is_new_connection:
            self.db.add(connection)

        if token_response.whoop_user_id is not None:
            connection.whoop_user_id = token_response.whoop_user_id
        connection.status = "connected"
        connection.access_token_encrypted = encrypt_secret(
            token_response.access_token,
            self.settings.app_encryption_key,
        )
        connection.refresh_token_encrypted = refresh_token_encrypted
        connection.token_expires_at_utc = now + timedelta(seconds=token_response.expires_in)
        connection.granted_scopes = token_response.scope
        connection.connected_at_utc = connection.connected_at_utc or now
        if refreshed:
            connection.last_token_refresh_at_utc = now
        connection.updated_at_utc = now
        self.db.commit()
        self.db.refresh(connection)
        logger.info(
            "whoop.tokens.saved refreshed=%s expires_at=%s scope_present=%s user_id_present=%s",
            refreshed,
            connection.token_expires_at_utc.isoformat(),
            connection.granted_scopes is not None,
            connection.whoop_user_id is not None,
        )
        return connection

    def mark_error(self) -> None:
        connection = self.get_connection()
        if connection is None:
            return
        connection.status = "error"
        connection.updated_at_utc = datetime.now(UTC)
        self.db.commit()
        logger.warning("whoop.tokens.connection_marked_error")

    def refresh_if_needed(
        self,
        oauth_client,
        *,
        buffer_seconds: int = 300,
    ) -> StoredWhoopTokens | None:
        connection = self.get_connection()
        if connection is None:
            return None

        tokens = self.get_decrypted_tokens()
        if tokens is None:
            return None

        refresh_at = datetime.now(UTC) + timedelta(seconds=buffer_seconds)
        if ensure_utc(connection.token_expires_at_utc) > refresh_at:
            return tokens

        return self.refresh_now(oauth_client, tokens=tokens)

    def refresh_now(
        self,
        oauth_client,
        *,
        tokens: StoredWhoopTokens | None = None,
    ) -> StoredWhoopTokens | None:
        tokens = tokens or self.get_decrypted_tokens()
        if tokens is None:
            return None
        if not tokens.refresh_token:
            self.mark_error()
            raise WhoopTokenRefreshError("WHOOP refresh token is missing; reconnect WHOOP")

        try:
            logger.info("whoop.tokens.refresh.start")
            token_response = oauth_client.refresh_tokens(tokens.refresh_token)
        except Exception as exc:
            self.mark_error()
            logger.warning("whoop.tokens.refresh.failed error_type=%s", exc.__class__.__name__)
            raise WhoopTokenRefreshError("WHOOP token refresh failed") from exc

        self.save_token_response(token_response, refreshed=True)
        logger.info("whoop.tokens.refresh.success")
        return self.get_decrypted_tokens()

    def get_decrypted_tokens(self) -> StoredWhoopTokens | None:
        connection = self.get_connection()
        if connection is None:
            return None
        # P6-S4 is the only intended caller for decrypted tokens outside tests.
        # Do not expose this result through API schemas or logs.
        return StoredWhoopTokens(
            access_token=decrypt_secret(
                connection.access_token_encrypted,
                self.settings.app_encryption_key,
            ),
            refresh_token=decrypt_secret(
                connection.refresh_token_encrypted,
                self.settings.app_encryption_key,
            ),
            expires_at_utc=ensure_utc(connection.token_expires_at_utc),
            granted_scopes=connection.granted_scopes,
        )

    def disconnect(self) -> None:
        self.db.execute(delete(WhoopConnectionModel))
        self.db.commit()
