from collections.abc import Sequence
from typing import Literal

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.repositories.sync import SyncRepository
from app.schemas.sync import (
    SyncCounts,
    SyncResourceOutcome,
    SyncRunSummary,
    SyncStatus,
    SyncStatusValue,
)
from app.services.sync.orchestrator import SyncOrchestrator, SyncOutcome
from app.services.whoop.client import WhoopOAuthClient
from app.services.whoop.provider_client import WhoopProviderClient
from app.services.whoop.token_store import WhoopTokenStore

RunResourceType = Literal["workouts", "sleeps", "recoveries", "all"]


class SyncAlreadyRunningError(RuntimeError):
    pass


def build_sync_orchestrator(
    db: Session,
    *,
    settings: Settings | None = None,
    provider_client=None,
) -> SyncOrchestrator:
    settings = settings or get_settings()
    if provider_client is not None:
        return SyncOrchestrator(db, provider_client)

    token_store = WhoopTokenStore(db, settings)
    oauth_client = WhoopOAuthClient(settings)
    whoop_provider = WhoopProviderClient(
        settings=settings,
        token_store=token_store,
        oauth_client=oauth_client,
    )
    return SyncOrchestrator(db, whoop_provider)


def run_manual_sync(
    db: Session,
    *,
    resource_type: RunResourceType = "all",
    settings: Settings | None = None,
    provider_client=None,
) -> list[SyncOutcome]:
    _raise_if_running(db)
    orchestrator = build_sync_orchestrator(
        db,
        settings=settings,
        provider_client=provider_client,
    )
    if resource_type == "all":
        return orchestrator.sync_all(trigger="manual")
    return [orchestrator.sync_resource(resource_type=resource_type, trigger="manual")]


def run_scheduled_sync(
    db: Session,
    *,
    resource_type: RunResourceType = "all",
    settings: Settings | None = None,
    provider_client=None,
) -> list[SyncOutcome]:
    _raise_if_running(db)
    orchestrator = build_sync_orchestrator(
        db,
        settings=settings,
        provider_client=provider_client,
    )
    if resource_type == "all":
        return orchestrator.sync_all(trigger="scheduled")
    return [orchestrator.sync_resource(resource_type=resource_type, trigger="scheduled")]


def build_sync_status(
    db: Session,
    *,
    settings: Settings | None = None,
    outcomes: Sequence[SyncOutcome] | None = None,
) -> SyncStatus:
    settings = settings or get_settings()
    repository = SyncRepository(db)
    latest_running = repository.get_latest_running_run()
    latest_run = latest_running or repository.get_latest_run()
    states = repository.get_states()
    last_success = max(
        (
            state.last_successful_sync_at_utc
            for state in states
            if state.last_successful_sync_at_utc is not None
        ),
        default=None,
    )

    if outcomes is not None:
        status = _aggregate_outcome_status(outcomes)
        latest_run = repository.get_latest_run()
        message = _message_for_status(status)
    elif latest_running is not None:
        status = "running"
        message = "Sync is currently running."
    elif latest_run is not None:
        status = _status_from_run(latest_run.status)
        message = _message_for_status(status)
    else:
        status = "idle"
        message = "No sync runs have been recorded yet."

    return SyncStatus(
        status=status,
        auto_sync_enabled=settings.auto_sync_enabled,
        auto_sync_frequency=settings.auto_sync_frequency,
        last_success_at_utc=last_success,
        latest_run=_run_summary(latest_run),
        outcomes=[_outcome_summary(outcome) for outcome in outcomes or []],
        counts=_status_counts(outcomes=outcomes, latest_run=latest_run),
        message=message,
    )


def _raise_if_running(db: Session) -> None:
    if SyncRepository(db).get_latest_running_run() is not None:
        raise SyncAlreadyRunningError("A sync run is already in progress.")


def _run_summary(row) -> SyncRunSummary | None:
    if row is None:
        return None
    return SyncRunSummary(
        id=row.id,
        resource_type=row.resource_type,
        trigger=row.trigger,
        status=row.status,
        window_start_utc=row.window_start_utc,
        window_end_utc=row.window_end_utc,
        inserted_count=row.inserted_count,
        updated_count=row.updated_count,
        unchanged_count=row.unchanged_count,
        failed_count=row.failed_count,
        started_at_utc=row.started_at_utc,
        finished_at_utc=row.finished_at_utc,
        error_message=row.error_message,
    )


def _outcome_summary(outcome: SyncOutcome) -> SyncResourceOutcome:
    return SyncResourceOutcome(
        resource_type=outcome.resource_type,
        status=outcome.status,
        counts=SyncCounts(
            inserted=outcome.counts.inserted,
            updated=outcome.counts.updated,
            unchanged=outcome.counts.unchanged,
            failed=outcome.counts.failed,
        ),
        run_id=outcome.run_id,
        window_start_utc=outcome.window_start_utc,
        window_end_utc=outcome.window_end_utc,
        error_message=outcome.error_message,
    )


def _aggregate_counts(outcomes: Sequence[SyncOutcome]) -> SyncCounts:
    return SyncCounts(
        inserted=sum(outcome.counts.inserted for outcome in outcomes),
        updated=sum(outcome.counts.updated for outcome in outcomes),
        unchanged=sum(outcome.counts.unchanged for outcome in outcomes),
        failed=sum(outcome.counts.failed for outcome in outcomes),
    )


def _status_counts(
    *,
    outcomes: Sequence[SyncOutcome] | None,
    latest_run,
) -> SyncCounts:
    if outcomes is not None:
        return _aggregate_counts(outcomes)
    if latest_run is None:
        return SyncCounts()
    return SyncCounts(
        inserted=latest_run.inserted_count,
        updated=latest_run.updated_count,
        unchanged=latest_run.unchanged_count,
        failed=latest_run.failed_count,
    )


def _aggregate_outcome_status(outcomes: Sequence[SyncOutcome]) -> SyncStatusValue:
    if not outcomes:
        return "idle"
    statuses = {outcome.status for outcome in outcomes}
    if statuses == {"success"}:
        return "success"
    if "partial" in statuses or ("success" in statuses and "failed" in statuses):
        return "partial"
    if statuses == {"failed"}:
        return "failed"
    return "partial"


def _status_from_run(status: str) -> SyncStatusValue:
    if status in {"running", "success", "partial", "failed"}:
        return status  # type: ignore[return-value]
    return "idle"


def _message_for_status(status: SyncStatusValue) -> str:
    if status == "running":
        return "Sync is currently running."
    if status == "success":
        return "Sync completed successfully."
    if status == "partial":
        return "Sync completed with some records skipped."
    if status == "failed":
        return "Sync failed before it could complete."
    return "Sync engine is idle."
