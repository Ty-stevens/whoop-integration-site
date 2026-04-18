from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from json import JSONDecodeError
from time import sleep
from typing import Any

import httpx

from app.core.config import Settings
from app.core.time import ensure_utc
from app.services.whoop.client import WhoopOAuthClient
from app.services.whoop.provider_models import (
    WhoopRecoveryCollectionResponse,
    WhoopSleepCollectionResponse,
    WhoopWorkoutCollectionResponse,
)
from app.services.whoop.token_store import WhoopTokenRefreshError, WhoopTokenStore

CollectionModel = (
    WhoopWorkoutCollectionResponse | WhoopSleepCollectionResponse | WhoopRecoveryCollectionResponse
)
CollectionParser = Callable[[dict[str, Any]], CollectionModel]


class WhoopProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class WhoopCollectionPage:
    raw_payload: dict[str, Any]
    parsed: CollectionModel


class WhoopProviderClient:
    def __init__(
        self,
        settings: Settings,
        token_store: WhoopTokenStore,
        oauth_client: WhoopOAuthClient,
        http_client: httpx.Client | None = None,
        *,
        refresh_buffer_seconds: int = 300,
        max_transient_retries: int = 2,
        retry_delay_seconds: float = 0.2,
    ) -> None:
        self.settings = settings
        self.token_store = token_store
        self.oauth_client = oauth_client
        self.http_client = http_client
        self.refresh_buffer_seconds = refresh_buffer_seconds
        self.max_transient_retries = max_transient_retries
        self.retry_delay_seconds = retry_delay_seconds

    def fetch_workouts(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 25,
    ) -> list[WhoopCollectionPage]:
        return self._fetch_collection(
            path="/v2/activity/workout",
            parser=WhoopWorkoutCollectionResponse.model_validate,
            start=start,
            end=end,
            limit=limit,
        )

    def fetch_sleeps(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 25,
    ) -> list[WhoopCollectionPage]:
        return self._fetch_collection(
            path="/v2/activity/sleep",
            parser=WhoopSleepCollectionResponse.model_validate,
            start=start,
            end=end,
            limit=limit,
        )

    def fetch_recoveries(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 25,
    ) -> list[WhoopCollectionPage]:
        return self._fetch_collection(
            path="/v2/recovery",
            parser=WhoopRecoveryCollectionResponse.model_validate,
            start=start,
            end=end,
            limit=limit,
        )

    def _fetch_collection(
        self,
        *,
        path: str,
        parser: CollectionParser,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[WhoopCollectionPage]:
        if limit < 1 or limit > 25:
            raise WhoopProviderError("WHOOP collection limit must be between 1 and 25")

        pages: list[WhoopCollectionPage] = []
        next_token: str | None = None
        seen_next_tokens: set[str] = set()

        while True:
            raw_payload = self._get_json(
                path,
                params=self._collection_params(
                    start=start,
                    end=end,
                    limit=limit,
                    next_token=next_token,
                ),
            )
            parsed = parser(raw_payload)
            pages.append(WhoopCollectionPage(raw_payload=raw_payload, parsed=parsed))
            next_token = parsed.next_token
            if next_token is None:
                return pages
            if next_token in seen_next_tokens:
                raise WhoopProviderError("WHOOP pagination returned a repeated next token")
            seen_next_tokens.add(next_token)

    def _get_json(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        try:
            tokens = self.token_store.refresh_if_needed(
                self.oauth_client,
                buffer_seconds=self.refresh_buffer_seconds,
            )
        except WhoopTokenRefreshError as exc:
            raise WhoopProviderError("WHOOP token refresh failed") from exc
        if tokens is None:
            raise WhoopProviderError("WHOOP connection is not available")

        retried_after_unauthorized = False
        transient_attempts = 0

        while True:
            try:
                response = self._request_with_token(
                    path,
                    params=params,
                    access_token=tokens.access_token,
                )
            except httpx.HTTPError as exc:
                raise WhoopProviderError("WHOOP provider request failed") from exc

            if response.status_code == 401 and not retried_after_unauthorized:
                try:
                    refreshed_tokens = self.token_store.refresh_now(
                        self.oauth_client,
                        tokens=tokens,
                    )
                except WhoopTokenRefreshError as exc:
                    raise WhoopProviderError("WHOOP token refresh failed after 401") from exc
                if refreshed_tokens is None:
                    raise WhoopProviderError("WHOOP connection is not available")
                tokens = refreshed_tokens
                retried_after_unauthorized = True
                continue

            if response.status_code in {429, 500, 502, 503, 504}:
                if transient_attempts < self.max_transient_retries:
                    transient_attempts += 1
                    if self.retry_delay_seconds > 0:
                        sleep(self.retry_delay_seconds)
                    continue
                raise WhoopProviderError(
                    f"WHOOP provider request failed with {response.status_code}"
                )

            if response.is_error:
                raise WhoopProviderError(
                    f"WHOOP provider request failed with {response.status_code}"
                )

            try:
                data = response.json()
            except JSONDecodeError as exc:
                raise WhoopProviderError("WHOOP provider response was not valid JSON") from exc
            if not isinstance(data, dict):
                raise WhoopProviderError("WHOOP provider response was not a JSON object")
            return data

    def _request_with_token(
        self,
        path: str,
        *,
        params: dict[str, Any],
        access_token: str,
    ) -> httpx.Response:
        client = self.http_client
        url = f"{self.settings.whoop_api_base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {access_token}"}
        if client is not None:
            return client.get(url, params=params, headers=headers, timeout=15)
        with httpx.Client(timeout=15) as scoped_client:
            return scoped_client.get(url, params=params, headers=headers)

    def _collection_params(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        next_token: str | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if start is not None:
            params["start"] = ensure_utc(start).isoformat()
        if end is not None:
            params["end"] = ensure_utc(end).isoformat()
        if next_token is not None:
            params["nextToken"] = next_token
        return params
