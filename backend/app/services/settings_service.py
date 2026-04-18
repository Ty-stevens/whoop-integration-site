from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.settings import AppSettingsModel
from app.schemas.settings import AppSettings

SETTINGS_ROW_ID = 1


def default_app_settings() -> AppSettings:
    settings = get_settings()
    return AppSettings(
        auto_sync_enabled=settings.auto_sync_enabled,
        auto_sync_frequency=settings.auto_sync_frequency,
    )


def _to_schema(row: AppSettingsModel) -> AppSettings:
    return AppSettings(
        auto_sync_enabled=row.auto_sync_enabled,
        auto_sync_frequency=row.auto_sync_frequency,  # type: ignore[arg-type]
        preferred_export_format=row.preferred_export_format,  # type: ignore[arg-type]
        preferred_units=row.preferred_units,  # type: ignore[arg-type]
    )


def get_app_settings(db: Session) -> AppSettings:
    row = db.get(AppSettingsModel, SETTINGS_ROW_ID)
    if row is None:
        return default_app_settings()
    return _to_schema(row)


def upsert_app_settings(db: Session, payload: AppSettings) -> AppSettings:
    row = db.get(AppSettingsModel, SETTINGS_ROW_ID)
    if row is None:
        row = AppSettingsModel(id=SETTINGS_ROW_ID)
        db.add(row)

    row.auto_sync_enabled = payload.auto_sync_enabled
    row.auto_sync_frequency = payload.auto_sync_frequency
    row.preferred_export_format = payload.preferred_export_format
    row.preferred_units = payload.preferred_units
    row.updated_at_utc = datetime.now(UTC)
    db.commit()
    db.refresh(row)
    return _to_schema(row)

