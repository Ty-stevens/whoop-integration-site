import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.core.time import ensure_utc
from app.repositories.recoveries import RecoveryRepository
from app.repositories.sleeps import SleepRepository
from app.repositories.sync import SyncRepository
from app.repositories.workouts import WorkoutRepository
from app.services.whoop.provider_client import WhoopCollectionPage
from app.services.whoop.transformers import transform_recovery, transform_sleep, transform_workout

SyncResourceType = Literal["workouts", "sleeps", "recoveries"]
SyncTrigger = Literal["initial_backfill", "manual", "scheduled"]

BACKFILL_DAYS = 180
OVERLAP_DAYS = 3
TOKEN_SAFE_ERROR_LIMIT = 240
logger = logging.getLogger("endurasync.sync")


@dataclass(frozen=True)
class SyncCounts:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    failed: int = 0


@dataclass(frozen=True)
class SyncOutcome:
    run_id: int
    resource_type: SyncResourceType
    trigger: SyncTrigger
    status: str
    window_start_utc: datetime
    window_end_utc: datetime
    counts: SyncCounts
    error_message: str | None = None


@dataclass(frozen=True)
class ResourceSyncSpec:
    fetch_method_name: str
    repository_type: type
    transform: Callable[[Any, dict[str, Any]], dict[str, Any]]


RESOURCE_SPECS: dict[SyncResourceType, ResourceSyncSpec] = {
    "workouts": ResourceSyncSpec("fetch_workouts", WorkoutRepository, transform_workout),
    "sleeps": ResourceSyncSpec("fetch_sleeps", SleepRepository, transform_sleep),
    "recoveries": ResourceSyncSpec("fetch_recoveries", RecoveryRepository, transform_recovery),
}


class SyncOrchestrator:
    def __init__(
        self,
        db: Session,
        provider_client: Any,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.db = db
        self.provider_client = provider_client
        self.clock = clock or (lambda: datetime.now(UTC))
        self.sync_repository = SyncRepository(db)

    def sync_all(self, *, trigger: SyncTrigger = "manual") -> list[SyncOutcome]:
        return [
            self.sync_resource(resource_type="workouts", trigger=trigger),
            self.sync_resource(resource_type="sleeps", trigger=trigger),
            self.sync_resource(resource_type="recoveries", trigger=trigger),
        ]

    def sync_resource(
        self,
        *,
        resource_type: SyncResourceType,
        trigger: SyncTrigger,
    ) -> SyncOutcome:
        spec = RESOURCE_SPECS[resource_type]
        window_start, window_end = self._window_for(resource_type=resource_type, trigger=trigger)
        run = self.sync_repository.create_run(
            trigger=trigger,
            resource_type=resource_type,
            window_start_utc=window_start,
            window_end_utc=window_end,
        )
        logger.info(
            "sync.resource.start run_id=%s resource=%s trigger=%s window_start=%s window_end=%s",
            run.id,
            resource_type,
            trigger,
            window_start.isoformat(),
            window_end.isoformat(),
        )

        counts = {"inserted": 0, "updated": 0, "unchanged": 0, "failed": 0}
        error_messages: list[str] = []

        try:
            fetch = getattr(self.provider_client, spec.fetch_method_name)
            pages = fetch(start=window_start, end=window_end, limit=25)
        except Exception as exc:
            message = _token_safe_error_message(exc)
            self.sync_repository.finish_run(run, status="failed", error_message=message)
            logger.warning(
                "sync.resource.fetch_failed run_id=%s resource=%s error=%s",
                run.id,
                resource_type,
                message,
            )
            return SyncOutcome(
                run_id=run.id,
                resource_type=resource_type,
                trigger=trigger,
                status="failed",
                window_start_utc=window_start,
                window_end_utc=window_end,
                counts=SyncCounts(),
                error_message=message,
            )

        repository = spec.repository_type(self.db)
        for page in pages:
            if page.invalid_record_errors:
                counts["failed"] += len(page.invalid_record_errors)
                error_messages.extend(
                    _token_safe_error_message(ValueError(error))
                    for error in page.invalid_record_errors
                )
            for index, provider_record in enumerate(page.parsed.records):
                try:
                    raw_record = self._raw_record_at(page, index)
                    values = spec.transform(provider_record, raw_record)
                    result = repository.upsert(values)
                except Exception as exc:
                    self.db.rollback()
                    counts["failed"] += 1
                    error_messages.append(_token_safe_error_message(exc))
                    continue

                if result.inserted:
                    counts["inserted"] += 1
                elif result.updated:
                    counts["updated"] += 1
                elif result.unchanged:
                    counts["unchanged"] += 1

        status = "partial" if counts["failed"] else "success"
        successful_records = counts["inserted"] + counts["updated"] + counts["unchanged"]
        error_message = "; ".join(error_messages[:3]) if error_messages else None
        if error_message is not None:
            error_message = error_message[:TOKEN_SAFE_ERROR_LIMIT]

        self.sync_repository.finish_run(
            run,
            status=status,
            inserted_count=counts["inserted"],
            updated_count=counts["updated"],
            unchanged_count=counts["unchanged"],
            failed_count=counts["failed"],
            error_message=error_message,
        )

        if status == "success" or successful_records > 0:
            previous_state = self.sync_repository.get_state(resource_type)
            self.sync_repository.upsert_state(
                resource_type=resource_type,
                last_successful_sync_at_utc=window_end
                if status == "success"
                else (
                    previous_state.last_successful_sync_at_utc
                    if previous_state is not None
                    else None
                ),
                last_window_start_utc=window_start,
                last_window_end_utc=window_end,
                cursor_text=None,
            )
        logger.info(
            "sync.resource.finish run_id=%s resource=%s status=%s "
            "inserted=%s updated=%s unchanged=%s failed=%s",
            run.id,
            resource_type,
            status,
            counts["inserted"],
            counts["updated"],
            counts["unchanged"],
            counts["failed"],
        )

        return SyncOutcome(
            run_id=run.id,
            resource_type=resource_type,
            trigger=trigger,
            status=status,
            window_start_utc=window_start,
            window_end_utc=window_end,
            counts=SyncCounts(**counts),
            error_message=error_message,
        )

    def _window_for(
        self,
        *,
        resource_type: SyncResourceType,
        trigger: SyncTrigger,
    ) -> tuple[datetime, datetime]:
        window_end = ensure_utc(self.clock())
        state = self.sync_repository.get_state(resource_type)
        if trigger != "initial_backfill" and state is not None and state.last_window_end_utc:
            window_start = ensure_utc(state.last_window_end_utc) - timedelta(days=OVERLAP_DAYS)
        else:
            window_start = window_end - timedelta(days=BACKFILL_DAYS)
        return window_start, window_end

    def _raw_record_at(self, page: WhoopCollectionPage, index: int) -> dict[str, Any]:
        raw_records = page.raw_payload.get("records")
        if not isinstance(raw_records, list):
            raise ValueError("WHOOP page raw records are missing")
        if index >= len(raw_records):
            raise ValueError("WHOOP raw record is missing for parsed record")
        raw_record = raw_records[index]
        if not isinstance(raw_record, dict):
            raise ValueError("WHOOP raw record is not a JSON object")
        return raw_record


def _token_safe_error_message(exc: Exception) -> str:
    message = str(exc) or exc.__class__.__name__
    banned_fragments = [
        "access_token",
        "refresh_token",
        "access-token",
        "refresh-token",
        "Authorization",
        "Bearer ",
    ]
    for fragment in banned_fragments:
        message = message.replace(fragment, "[redacted]")
    return message[:TOKEN_SAFE_ERROR_LIMIT]
