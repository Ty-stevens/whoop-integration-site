from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.settings import AppSettings
from app.services.settings_service import get_app_settings, upsert_app_settings

router = APIRouter()


@router.get("", response_model=AppSettings)
def read_settings(db: DbSession) -> AppSettings:
    return get_app_settings(db)


@router.put("", response_model=AppSettings)
def update_settings(payload: AppSettings, db: DbSession) -> AppSettings:
    return upsert_app_settings(db, payload)
