from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SyncResourceType = Literal["workouts", "sleeps", "recoveries", "all"]
SyncStatusValue = Literal["idle", "running", "success", "partial", "failed"]


class SyncRunRequest(BaseModel):
    resource_type: SyncResourceType = "all"


class SyncCounts(BaseModel):
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    failed: int = 0


class SyncRunSummary(BaseModel):
    id: int
    resource_type: str | None = None
    trigger: str
    status: str
    window_start_utc: datetime | None = None
    window_end_utc: datetime | None = None
    inserted_count: int = 0
    updated_count: int = 0
    unchanged_count: int = 0
    failed_count: int = 0
    started_at_utc: datetime | None = None
    finished_at_utc: datetime | None = None
    error_message: str | None = None


class SyncResourceOutcome(BaseModel):
    resource_type: Literal["workouts", "sleeps", "recoveries"]
    status: str
    counts: SyncCounts
    run_id: int
    window_start_utc: datetime
    window_end_utc: datetime
    error_message: str | None = None


class SyncStatus(BaseModel):
    status: SyncStatusValue = "idle"
    auto_sync_enabled: bool = False
    auto_sync_frequency: Literal["daily", "twice_daily"] = "daily"
    last_success_at_utc: datetime | None = None
    latest_run: SyncRunSummary | None = None
    outcomes: list[SyncResourceOutcome] = []
    counts: SyncCounts = SyncCounts()
    message: str = "Sync engine is idle."
