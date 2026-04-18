from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.time import ensure_utc
from app.models.facts import RecoveryModel, WorkoutModel
from app.repositories.goals import GoalRepository
from app.repositories.sync import SyncRepository
from app.services.metrics.types import (
    CurrentWeekSummary,
    MetricsError,
    SessionProgress,
    ZoneProgress,
)


class CurrentWeekMetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, week_start_date: date) -> CurrentWeekSummary:
        if week_start_date.weekday() != 0:
            raise MetricsError("week_start_date must be a Monday ISO week start")

        workouts = (
            self.db.query(WorkoutModel)
            .filter(WorkoutModel.iso_week_start_date == week_start_date)
            .all()
        )
        recoveries = (
            self.db.query(RecoveryModel)
            .filter(RecoveryModel.iso_week_start_date == week_start_date)
            .all()
        )
        goal = GoalRepository(self.db).active_for_week(week_start_date)
        sync_states = SyncRepository(self.db).get_states()
        last_success = max(
            (
                state.last_successful_sync_at_utc
                for state in sync_states
                if state.last_successful_sync_at_utc is not None
            ),
            default=None,
        )

        zone_targets = _goal_zone_targets(goal)
        zones = [
            _zone_progress(
                zone=zone,
                actual_seconds=sum(getattr(workout, f"zone{zone}_seconds") for workout in workouts),
                target_minutes=zone_targets[zone],
            )
            for zone in range(1, 6)
        ]

        cardio_completed = sum(1 for workout in workouts if workout.classification == "cardio")
        strength_completed = sum(1 for workout in workouts if workout.classification == "strength")

        return CurrentWeekSummary(
            week_start_date=week_start_date,
            week_end_date=week_start_date + timedelta(days=6),
            has_goal_profile=goal is not None,
            goal_profile_id=goal.id if goal is not None else None,
            last_successful_sync_at_utc=ensure_utc(last_success)
            if last_success is not None
            else None,
            zones=zones,
            cardio_sessions=_session_progress(
                completed=cardio_completed,
                target=goal.cardio_sessions_target if goal is not None else 0,
            ),
            strength_sessions=_session_progress(
                completed=strength_completed,
                target=goal.strength_sessions_target if goal is not None else 0,
            ),
            total_training_seconds=sum(workout.duration_seconds for workout in workouts),
            average_recovery_score=_average(
                recovery.recovery_score
                for recovery in recoveries
                if recovery.recovery_score is not None
            ),
            average_daily_strain=_average(
                workout.strain for workout in workouts if workout.strain is not None
            ),
        )


def _goal_zone_targets(goal) -> dict[int, int]:
    if goal is None:
        return {zone: 0 for zone in range(1, 6)}
    return {
        1: goal.zone1_target_minutes,
        2: goal.zone2_target_minutes,
        3: goal.zone3_target_minutes,
        4: goal.zone4_target_minutes,
        5: goal.zone5_target_minutes,
    }


def _zone_progress(*, zone: int, actual_seconds: int, target_minutes: int) -> ZoneProgress:
    actual_minutes = actual_seconds // 60
    return ZoneProgress(
        zone=zone,
        actual_seconds=actual_seconds,
        actual_minutes=actual_minutes,
        target_minutes=target_minutes,
        percent_complete=_percent_complete(actual_minutes, target_minutes),
        remaining_minutes=max(target_minutes - actual_minutes, 0),
        exceeded=actual_seconds > 0 if target_minutes == 0 else actual_minutes >= target_minutes,
    )


def _session_progress(*, completed: int, target: int) -> SessionProgress:
    return SessionProgress(
        completed=completed,
        target=target,
        remaining=max(target - completed, 0),
        percent_complete=_percent_complete(completed, target),
    )


def _percent_complete(actual: int, target: int) -> float | None:
    if target == 0:
        return None
    return round((actual / target) * 100, 2)


def _average(values) -> float | None:
    values = list(values)
    if not values:
        return None
    decimal_values = [Decimal(value) for value in values]
    return round(float(sum(decimal_values) / len(decimal_values)), 2)
