from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.time import iso_week_start
from app.models.facts import RecoveryModel, SleepModel, WorkoutModel
from app.services.metrics.types import (
    ConsistencySummary,
    MonthlyTrainingSummary,
    SixMonthReportSummary,
)

REPORT_MONTHS = 6


class SixMonthReportMetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, as_of_date: date) -> SixMonthReportSummary:
        end_month = date(as_of_date.year, as_of_date.month, 1)
        start_month = _shift_months(end_month, -(REPORT_MONTHS - 1))
        month_starts = [_shift_months(start_month, offset) for offset in range(REPORT_MONTHS)]
        range_end_date = _month_end(end_month)

        workouts = self._workouts_in_range(start_month, end_month)
        sleeps = self._sleeps_in_range(start_month, end_month)
        recoveries = self._recoveries_in_range(start_month, end_month)

        workouts_by_month = _group_by(workouts, "local_month_start_date")
        sleeps_by_month = _group_by(sleeps, "local_month_start_date")
        recoveries_by_month = _group_by(recoveries, "local_month_start_date")

        monthly_summaries = [
            self._build_month_summary(
                month_start,
                workouts_by_month.get(month_start, []),
                sleeps_by_month.get(month_start, []),
                recoveries_by_month.get(month_start, []),
            )
            for month_start in month_starts
        ]

        consistency_summary = self._build_consistency_summary(
            start_month=start_month,
            range_end_date=range_end_date,
            workouts=workouts,
            sleeps=sleeps,
            recoveries=recoveries,
        )

        return SixMonthReportSummary(
            range_start_date=start_month,
            range_end_date=range_end_date,
            month_count=REPORT_MONTHS,
            monthly_summaries=monthly_summaries,
            consistency_summary=consistency_summary,
        )

    def _workouts_in_range(self, start_month: date, end_month: date) -> list[WorkoutModel]:
        return (
            self.db.query(WorkoutModel)
            .filter(
                WorkoutModel.local_month_start_date >= start_month,
                WorkoutModel.local_month_start_date <= end_month,
            )
            .order_by(WorkoutModel.local_month_start_date.asc(), WorkoutModel.id.asc())
            .all()
        )

    def _sleeps_in_range(self, start_month: date, end_month: date) -> list[SleepModel]:
        return (
            self.db.query(SleepModel)
            .filter(
                SleepModel.local_month_start_date >= start_month,
                SleepModel.local_month_start_date <= end_month,
            )
            .order_by(SleepModel.local_month_start_date.asc(), SleepModel.id.asc())
            .all()
        )

    def _recoveries_in_range(self, start_month: date, end_month: date) -> list[RecoveryModel]:
        return (
            self.db.query(RecoveryModel)
            .filter(
                RecoveryModel.local_month_start_date >= start_month,
                RecoveryModel.local_month_start_date <= end_month,
            )
            .order_by(RecoveryModel.local_month_start_date.asc(), RecoveryModel.id.asc())
            .all()
        )

    def _build_month_summary(
        self,
        month_start: date,
        workouts: list[WorkoutModel],
        sleeps: list[SleepModel],
        recoveries: list[RecoveryModel],
    ) -> MonthlyTrainingSummary:
        zone_seconds = {
            zone: sum(getattr(workout, f"zone{zone}_seconds") for workout in workouts)
            for zone in range(1, 6)
        }
        classification_counts = defaultdict(int)
        for workout in workouts:
            classification_counts[workout.classification or "unknown"] += 1

        return MonthlyTrainingSummary(
            month_start_date=month_start,
            month_end_date=_month_end(month_start),
            month_label=month_start.strftime("%b %Y"),
            workout_count=len(workouts),
            sleep_count=len(sleeps),
            recovery_count=len(recoveries),
            training_seconds=sum(workout.duration_seconds for workout in workouts),
            zone1_minutes=zone_seconds[1] // 60,
            zone2_minutes=zone_seconds[2] // 60,
            zone3_minutes=zone_seconds[3] // 60,
            zone4_minutes=zone_seconds[4] // 60,
            zone5_minutes=zone_seconds[5] // 60,
            cardio_count=classification_counts["cardio"],
            strength_count=classification_counts["strength"],
            other_count=classification_counts["other"],
            unknown_count=classification_counts["unknown"],
            average_recovery_score=_average_decimal(
                recovery.recovery_score
                for recovery in recoveries
                if recovery.recovery_score is not None
            ),
            average_daily_strain=_average_decimal(
                workout.strain for workout in workouts if workout.strain is not None
            ),
        )

    def _build_consistency_summary(
        self,
        *,
        start_month: date,
        range_end_date: date,
        workouts: list[WorkoutModel],
        sleeps: list[SleepModel],
        recoveries: list[RecoveryModel],
    ) -> ConsistencySummary:
        week_starts = _week_starts_in_range(start_month, range_end_date)
        workout_weeks = {workout.iso_week_start_date for workout in workouts}
        sleep_weeks = {sleep.iso_week_start_date for sleep in sleeps}
        recovery_weeks = {recovery.iso_week_start_date for recovery in recoveries}
        active_weeks = sum(
            1
            for week_start in week_starts
            if (
                week_start in workout_weeks
                or week_start in sleep_weeks
                or week_start in recovery_weeks
            )
        )
        weeks_with_workouts = len(workout_weeks)
        weeks_with_sleeps = len(sleep_weeks)
        weeks_with_recoveries = len(recovery_weeks)

        training_coverage = _coverage_percent(weeks_with_workouts, len(week_starts))
        sleep_coverage = _coverage_percent(weeks_with_sleeps, len(week_starts))
        recovery_coverage = _coverage_percent(weeks_with_recoveries, len(week_starts))

        if not active_weeks:
            summary_text = "No training, sleep, or recovery history landed in the six-month window."
        elif (
            training_coverage is not None
            and training_coverage >= 80
            and recovery_coverage is not None
            and recovery_coverage >= 80
        ):
            summary_text = (
                "Training and recovery are consistently present across the six-month window."
            )
        elif training_coverage is not None and training_coverage >= 50:
            summary_text = (
                "Training shows up regularly, but the window still has a few quiet weeks."
            )
        else:
            summary_text = (
                "The six-month window is still sparse, so consistency should be read "
                "cautiously."
            )

        return ConsistencySummary(
            weeks_in_range=len(week_starts),
            active_weeks=active_weeks,
            weeks_with_workouts=weeks_with_workouts,
            weeks_with_sleeps=weeks_with_sleeps,
            weeks_with_recoveries=weeks_with_recoveries,
            training_week_coverage_percent=training_coverage,
            sleep_week_coverage_percent=sleep_coverage,
            recovery_week_coverage_percent=recovery_coverage,
            summary_text=summary_text,
        )


def _group_by(rows: Iterable, field_name: str) -> dict[date, list]:
    grouped: dict[date, list] = {}
    for row in rows:
        grouped.setdefault(getattr(row, field_name), []).append(row)
    return grouped


def _average_decimal(values: Iterable[Decimal | float | int]) -> float | None:
    values = [float(value) for value in values]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _coverage_percent(part: int, whole: int) -> float | None:
    if whole == 0:
        return None
    return round((part / whole) * 100, 2)


def _shift_months(value: date, months: int) -> date:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def _month_end(value: date) -> date:
    next_month = _shift_months(value, 1)
    return next_month - timedelta(days=1)


def _week_starts_in_range(start_date: date, end_date: date) -> list[date]:
    start_week = iso_week_start(start_date)
    end_week = iso_week_start(end_date)
    week_starts: list[date] = []
    current = start_week
    while current <= end_week:
        week_starts.append(current)
        current += timedelta(days=7)
    return week_starts
