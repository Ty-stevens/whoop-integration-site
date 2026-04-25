import logging
from json import JSONDecodeError

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.services.whoop.models import WhoopTokenResponse

logger = logging.getLogger("endurasync.whoop.oauth")


class WhoopOAuthError(RuntimeError):
    pass


class WhoopOAuthClient:
    def __init__(self, settings: Settings, http_client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.http_client = http_client

    def exchange_code_for_tokens(self, code: str) -> WhoopTokenResponse:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.settings.whoop_redirect_uri,
            "client_id": self.settings.whoop_client_id,
            "client_secret": self.settings.whoop_client_secret,
        }
        return self._post_token_payload(payload, grant_type="authorization_code")

    def refresh_tokens(self, refresh_token: str) -> WhoopTokenResponse:
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.settings.whoop_client_id,
            "client_secret": self.settings.whoop_client_secret,
        }
        return self._post_token_payload(payload, grant_type="refresh_token")

    def _post_token_payload(
        self,
        payload: dict[str, str],
        *,
        grant_type: str,
    ) -> WhoopTokenResponse:
        logger.info("whoop.oauth.request grant_type=%s", grant_type)
        try:
            if self.http_client is not None:
                response = self.http_client.post(
                    self.settings.whoop_token_url,
                    data=payload,
                    timeout=15,
                )
            else:
                with httpx.Client(timeout=15) as client:
                    response = client.post(self.settings.whoop_token_url, data=payload)
            response.raise_for_status()
            data = response.json()
            token_response = WhoopTokenResponse.model_validate(data)
        except (httpx.HTTPError, JSONDecodeError, ValidationError, ValueError) as exc:
            logger.warning(
                "whoop.oauth.failed grant_type=%s error_type=%s",
                grant_type,
                exc.__class__.__name__,
            )
            raise WhoopOAuthError("WHOOP token endpoint returned an unusable response") from exc

        logger.info(
            "whoop.oauth.success grant_type=%s expires_in=%s scope_present=%s refresh_present=%s",
            grant_type,
            token_response.expires_in,
            token_response.scope is not None,
            token_response.refresh_token is not None,
        )
        return token_response
