from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_default() -> datetime:
    return datetime.now(UTC)


class WorkoutAnnotationModel(Base):
    __tablename__ = "workout_annotations"
    __table_args__ = (
        UniqueConstraint("workout_id", name="uq_workout_annotations_workout_id"),
        CheckConstraint(
            "manual_classification is null or manual_classification in "
            "('cardio', 'strength', 'other', 'unknown')",
            name="ck_workout_annotations_manual_classification",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    manual_classification: Mapped[str | None] = mapped_column(String(32))
    manual_strength_split: Mapped[str | None] = mapped_column(String(32))
    tag: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_default,
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_default,
        onupdate=utc_default,
    )


class GoalProfileModel(Base):
    __tablename__ = "goal_profiles"
    __table_args__ = (
        CheckConstraint("zone1_target_minutes >= 0", name="ck_goal_zone1_nonnegative"),
        CheckConstraint("zone2_target_minutes >= 0", name="ck_goal_zone2_nonnegative"),
        CheckConstraint("zone3_target_minutes >= 0", name="ck_goal_zone3_nonnegative"),
        CheckConstraint("zone4_target_minutes >= 0", name="ck_goal_zone4_nonnegative"),
        CheckConstraint("zone5_target_minutes >= 0", name="ck_goal_zone5_nonnegative"),
        CheckConstraint("cardio_sessions_target >= 0", name="ck_goal_cardio_nonnegative"),
        CheckConstraint("strength_sessions_target >= 0", name="ck_goal_strength_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effective_from_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_to_date: Mapped[date | None] = mapped_column(Date, index=True)
    zone1_target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zone2_target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=150)
    zone3_target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zone4_target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zone5_target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cardio_sessions_target: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    strength_sessions_target: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    created_reason: Mapped[str | None] = mapped_column(String(240))
    created_source: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    ai_provenance_json: Mapped[dict | None] = mapped_column(JSON)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_default,
    )


class SyncStateModel(Base):
    __tablename__ = "sync_state"
    __table_args__ = (UniqueConstraint("resource_type", name="uq_sync_state_resource_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    last_successful_sync_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_window_start_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_window_end_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor_text: Mapped[str | None] = mapped_column(Text)
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_default,
        onupdate=utc_default,
    )


class SyncRunModel(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    window_start_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_end_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_default,
    )
    finished_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
