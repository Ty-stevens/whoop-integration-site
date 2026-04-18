from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppSettingsModel(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    auto_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_sync_frequency: Mapped[str] = mapped_column(String(32), nullable=False, default="daily")
    preferred_export_format: Mapped[str] = mapped_column(String(16), nullable=False, default="csv")
    preferred_units: Mapped[str] = mapped_column(String(16), nullable=False, default="metric")
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

