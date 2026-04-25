import logging
from dataclasses import dataclass
from datetime import datetime
from json import JSONDecodeError
from time import sleep
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.core.time import ensure_utc
from app.services.whoop.client import WhoopOAuthClient
from app.services.whoop.provider_models import (
    WhoopRecovery,
    WhoopRecoveryCollectionResponse,
    WhoopSleep,
    WhoopSleepCollectionResponse,
    WhoopWorkout,
    WhoopWorkoutCollectionResponse,
)
from app.services.whoop.token_store import WhoopTokenRefreshError, WhoopTokenStore

CollectionModel = (
    WhoopWorkoutCollectionResponse | WhoopSleepCollectionResponse | WhoopRecoveryCollectionResponse
)
CollectionModelType = (
    type[WhoopWorkoutCollectionResponse]
    | type[WhoopSleepCollectionResponse]
    | type[WhoopRecoveryCollectionResponse]
)
RecordModelType = type[WhoopWorkout] | type[WhoopSleep] | type[WhoopRecovery]

logger = logging.getLogger("endurasync.whoop.provider")


class WhoopProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class WhoopCollectionPage:
    raw_payload: dict[str, Any]
    parsed: CollectionModel
    invalid_record_errors: tuple[str, ...] = ()


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
            resource_type="workouts",
            path="/v2/activity/workout",
            collection_model=WhoopWorkoutCollectionResponse,
            record_model=WhoopWorkout,
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
            resource_type="sleeps",
            path="/v2/activity/sleep",
            collection_model=WhoopSleepCollectionResponse,
            record_model=WhoopSleep,
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
            resource_type="recoveries",
            path="/v2/recovery",
            collection_model=WhoopRecoveryCollectionResponse,
            record_model=WhoopRecovery,
            start=start,
            end=end,
            limit=limit,
        )

    def _fetch_collection(
        self,
        *,
        resource_type: str,
        path: str,
        collection_model: CollectionModelType,
        record_model: RecordModelType,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[WhoopCollectionPage]:
        if limit < 1 or limit > 25:
            raise WhoopProviderError("WHOOP collection limit must be between 1 and 25")

        pages: list[WhoopCollectionPage] = []
        next_token: str | None = None
        seen_next_tokens: set[str] = set()
        logger.info(
            "whoop.fetch_collection.start resource=%s limit=%s start=%s end=%s",
            resource_type,
            limit,
            ensure_utc(start).isoformat() if start else None,
            ensure_utc(end).isoformat() if end else None,
        )

        while True:
            raw_payload = self._get_json(
                path,
                resource_type=resource_type,
                params=self._collection_params(
                    start=start,
                    end=end,
                    limit=limit,
                    next_token=next_token,
                ),
            )
            page = self._parse_collection_page(
                raw_payload,
                collection_model=collection_model,
                record_model=record_model,
                resource_type=resource_type,
            )
            pages.append(page)
            next_token = page.parsed.next_token
            if next_token is None:
                logger.info(
                    "whoop.fetch_collection.success resource=%s pages=%s "
                    "records=%s invalid_records=%s",
                    resource_type,
                    len(pages),
                    sum(len(page.parsed.records) for page in pages),
                    sum(len(page.invalid_record_errors) for page in pages),
                )
                return pages
            if next_token in seen_next_tokens:
                logger.warning(
                    "whoop.fetch_collection.repeated_next_token resource=%s",
                    resource_type,
                )
                raise WhoopProviderError("WHOOP pagination returned a repeated next token")
            seen_next_tokens.add(next_token)

    def _get_json(
        self,
        path: str,
        *,
        resource_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            tokens = self.token_store.refresh_if_needed(
                self.oauth_client,
                buffer_seconds=self.refresh_buffer_seconds,
            )
        except WhoopTokenRefreshError as exc:
            logger.warning("whoop.fetch.token_refresh_failed resource=%s", resource_type)
            raise WhoopProviderError("WHOOP token refresh failed") from exc
        if tokens is None:
            logger.warning("whoop.fetch.no_connection resource=%s", resource_type)
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
                logger.warning(
                    "whoop.fetch.http_error resource=%s error_type=%s",
                    resource_type,
                    exc.__class__.__name__,
                )
                raise WhoopProviderError("WHOOP provider request failed") from exc

            if response.status_code == 401 and not retried_after_unauthorized:
                logger.info("whoop.fetch.unauthorized_refresh resource=%s", resource_type)
                try:
                    refreshed_tokens = self.token_store.refresh_now(
                        self.oauth_client,
                        tokens=tokens,
                    )
                except WhoopTokenRefreshError as exc:
                    logger.warning(
                        "whoop.fetch.unauthorized_refresh_failed resource=%s",
                        resource_type,
                    )
                    raise WhoopProviderError("WHOOP token refresh failed after 401") from exc
                if refreshed_tokens is None:
                    logger.warning(
                        "whoop.fetch.no_connection_after_refresh resource=%s",
                        resource_type,
                    )
                    raise WhoopProviderError("WHOOP connection is not available")
                tokens = refreshed_tokens
                retried_after_unauthorized = True
                continue

            if response.status_code in {429, 500, 502, 503, 504}:
                if transient_attempts < self.max_transient_retries:
                    transient_attempts += 1
                    delay = self._retry_delay(response)
                    logger.info(
                        "whoop.fetch.retry resource=%s status_code=%s attempt=%s delay=%s",
                        resource_type,
                        response.status_code,
                        transient_attempts,
                        delay,
                    )
                    if delay > 0:
                        sleep(delay)
                    continue
                logger.warning(
                    "whoop.fetch.transient_exhausted resource=%s status_code=%s",
                    resource_type,
                    response.status_code,
                )
                raise WhoopProviderError(
                    f"WHOOP provider request failed with {response.status_code}"
                )

            if response.is_error:
                logger.warning(
                    "whoop.fetch.error_response resource=%s status_code=%s",
                    resource_type,
                    response.status_code,
                )
                raise WhoopProviderError(
                    f"WHOOP provider request failed with {response.status_code}"
                )

            try:
                data = response.json()
            except JSONDecodeError as exc:
                raise WhoopProviderError("WHOOP provider response was not valid JSON") from exc
            if not isinstance(data, dict):
                logger.warning("whoop.fetch.non_object_json resource=%s", resource_type)
                raise WhoopProviderError("WHOOP provider response was not a JSON object")
            return data

    def _parse_collection_page(
        self,
        raw_payload: dict[str, Any],
        *,
        collection_model: CollectionModelType,
        record_model: RecordModelType,
        resource_type: str,
    ) -> WhoopCollectionPage:
        raw_records = raw_payload.get("records")
        if not isinstance(raw_records, list):
            logger.warning("whoop.fetch.records_missing resource=%s", resource_type)
            raise WhoopProviderError("WHOOP provider response records were missing")

        records = []
        valid_raw_records: list[dict[str, Any]] = []
        invalid_record_errors: list[str] = []
        for index, raw_record in enumerate(raw_records):
            if not isinstance(raw_record, dict):
                invalid_record_errors.append(f"record[{index}] was not a JSON object")
                continue
            try:
                records.append(record_model.model_validate(raw_record))
                valid_raw_records.append(raw_record)
            except ValidationError as exc:
                invalid_record_errors.append(_validation_error_summary(index, exc))

        next_token = _next_token_from_payload(raw_payload)
        parsed = collection_model(records=records, next_token=next_token)
        if invalid_record_errors:
            logger.warning(
                "whoop.fetch.invalid_records resource=%s invalid_records=%s valid_records=%s",
                resource_type,
                len(invalid_record_errors),
                len(records),
            )
        return WhoopCollectionPage(
            raw_payload={**raw_payload, "records": valid_raw_records},
            parsed=parsed,
            invalid_record_errors=tuple(invalid_record_errors),
        )

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

    def _retry_delay(self, response: httpx.Response) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return max(float(retry_after), 0)
            except ValueError:
                return self.retry_delay_seconds
        return self.retry_delay_seconds


def _next_token_from_payload(raw_payload: dict[str, Any]) -> str | None:
    value = raw_payload.get("next_token")
    if value is None:
        value = raw_payload.get("nextToken")
    if value == "":
        return None
    if value is None:
        return None
    return str(value)


def _validation_error_summary(index: int, exc: ValidationError) -> str:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first_error.get("loc", ())) or "record"
    message = str(first_error.get("msg") or "validation failed")
    return f"record[{index}] {location}: {message}"[:240]
