from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.core.config import get_settings
from app.schemas.sync import SyncRunRequest, SyncStatus
from app.services.sync.service import (
    SyncAlreadyRunningError,
    build_sync_status,
    run_manual_sync,
)

router = APIRouter()


def get_sync_provider_client():
    return None


@router.get("/status", response_model=SyncStatus)
def sync_status(db: DbSession) -> SyncStatus:
    return build_sync_status(db, settings=get_settings())


@router.post("/run", response_model=SyncStatus)
def run_sync(payload: SyncRunRequest, db: DbSession) -> SyncStatus:
    settings = get_settings()
    try:
        outcomes = run_manual_sync(
            db,
            resource_type=payload.resource_type,
            settings=settings,
            provider_client=get_sync_provider_client(),
        )
    except SyncAlreadyRunningError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return build_sync_status(db, settings=settings, outcomes=outcomes)
