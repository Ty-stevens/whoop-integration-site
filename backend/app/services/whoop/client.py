import httpx

from app.core.config import Settings
from app.services.whoop.models import WhoopTokenResponse


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
        return self._post_token_payload(payload)

    def refresh_tokens(self, refresh_token: str) -> WhoopTokenResponse:
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.settings.whoop_client_id,
            "client_secret": self.settings.whoop_client_secret,
        }
        return self._post_token_payload(payload)

    def _post_token_payload(self, payload: dict[str, str]) -> WhoopTokenResponse:
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
        return WhoopTokenResponse.model_validate(response.json())
