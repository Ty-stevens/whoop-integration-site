from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_default() -> datetime:
    return datetime.now(UTC)


class WorkoutModel(Base):
    __tablename__ = "workouts"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_workouts_external_id"),
        CheckConstraint(
            "classification in ('cardio', 'strength', 'other', 'unknown')",
            name="ck_workouts_classification",
        ),
        CheckConstraint("duration_seconds >= 0", name="ck_workouts_duration_nonnegative"),
        CheckConstraint("zone0_seconds >= 0", name="ck_workouts_zone0_nonnegative"),
        CheckConstraint("zone1_seconds >= 0", name="ck_workouts_zone1_nonnegative"),
        CheckConstraint("zone2_seconds >= 0", name="ck_workouts_zone2_nonnegative"),
        CheckConstraint("zone3_seconds >= 0", name="ck_workouts_zone3_nonnegative"),
        CheckConstraint("zone4_seconds >= 0", name="ck_workouts_zone4_nonnegative"),
        CheckConstraint("zone5_seconds >= 0", name="ck_workouts_zone5_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    external_v1_id: Mapped[str | None] = mapped_column(String(128))
    whoop_user_id: Mapped[str | None] = mapped_column(String(128), index=True)
    external_created_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_updated_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone_offset_text: Mapped[str | None] = mapped_column(String(16))
    local_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    iso_week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    local_month_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    sport_name: Mapped[str | None] = mapped_column(String(120))
    score_state: Mapped[str | None] = mapped_column(String(64))
    classification: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    strain: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    average_hr: Mapped[int | None] = mapped_column(Integer)
    max_hr: Mapped[int | None] = mapped_column(Integer)
    percent_recorded: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    zone0_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zone1_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zone2_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zone3_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zone4_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zone5_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    source_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    imported_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_default,
    )


class SleepModel(Base):
    __tablename__ = "sleeps"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_sleeps_external_id"),
        CheckConstraint("sleep_duration_seconds >= 0", name="ck_sleeps_duration_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    external_v1_id: Mapped[str | None] = mapped_column(String(128))
    cycle_id: Mapped[str | None] = mapped_column(String(128), index=True)
    whoop_user_id: Mapped[str | None] = mapped_column(String(128), index=True)
    external_created_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_updated_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone_offset_text: Mapped[str | None] = mapped_column(String(16))
    local_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    iso_week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    local_month_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    nap: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score_state: Mapped[str | None] = mapped_column(String(64))
    sleep_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    sleep_performance: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    sleep_efficiency: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    raw_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    source_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    imported_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_default,
    )


class RecoveryModel(Base):
    __tablename__ = "recoveries"
    __table_args__ = (UniqueConstraint("cycle_id", name="uq_recoveries_cycle_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cycle_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sleep_external_id: Mapped[str | None] = mapped_column(String(128), index=True)
    whoop_user_id: Mapped[str | None] = mapped_column(String(128), index=True)
    external_created_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_updated_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    local_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    iso_week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    local_month_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    score_state: Mapped[str | None] = mapped_column(String(64))
    recovery_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    hrv_ms: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    resting_hr: Mapped[int | None] = mapped_column(Integer)
    respiratory_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    skin_temp_celsius: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    spo2_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    raw_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    source_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    imported_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_default,
    )

