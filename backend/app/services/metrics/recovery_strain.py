from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.time import iso_week_start
from app.models.facts import RecoveryModel, SleepModel, WorkoutModel
from app.services.metrics.types import (
    RecoveryStrainTrendsSummary,
    RollingComparisonCard,
    TrendWeeklyPoint,
)

TREND_WEEKS = 12
ROLLING_WINDOW_WEEKS = 4


class RecoveryStrainMetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, as_of_date: date) -> RecoveryStrainTrendsSummary:
        end_week = iso_week_start(as_of_date)
        start_week = end_week - timedelta(days=(TREND_WEEKS - 1) * 7)
        week_starts = [start_week + timedelta(days=7 * index) for index in range(TREND_WEEKS)]

        workouts = self._workouts_in_range(start_week, end_week)
        sleeps = self._sleeps_in_range(start_week, end_week)
        recoveries = self._recoveries_in_range(start_week, end_week)

        workouts_by_week = _group_by(workouts, "iso_week_start_date")
        sleeps_by_week = _group_by(sleeps, "iso_week_start_date")
        recoveries_by_week = _group_by(recoveries, "iso_week_start_date")

        weekly_series = [
            self._build_week_point(
                week_start,
                workouts_by_week.get(week_start, []),
                sleeps_by_week.get(week_start, []),
                recoveries_by_week.get(week_start, []),
            )
            for week_start in week_starts
        ]

        comparison_cards = [
            self._build_comparison_card(
                metric="recovery",
                label="Recovery",
                series=[point.average_recovery_score for point in weekly_series],
                current_points=weekly_series[-ROLLING_WINDOW_WEEKS:],
                previous_points=weekly_series[-ROLLING_WINDOW_WEEKS * 2 : -ROLLING_WINDOW_WEEKS],
            ),
            self._build_comparison_card(
                metric="strain",
                label="Strain",
                series=[point.average_daily_strain for point in weekly_series],
                current_points=weekly_series[-ROLLING_WINDOW_WEEKS:],
                previous_points=weekly_series[-ROLLING_WINDOW_WEEKS * 2 : -ROLLING_WINDOW_WEEKS],
            ),
        ]

        interpretation_text, data_state = self._interpretation(weekly_series, comparison_cards)

        return RecoveryStrainTrendsSummary(
            range_start_week=start_week,
            range_end_week=end_week,
            weekly_series=weekly_series,
            comparison_cards=comparison_cards,
            interpretation_text=interpretation_text,
            data_state=data_state,
        )

    def _workouts_in_range(self, start_week: date, end_week: date) -> list[WorkoutModel]:
        return (
            self.db.query(WorkoutModel)
            .filter(
                WorkoutModel.iso_week_start_date >= start_week,
                WorkoutModel.iso_week_start_date <= end_week,
            )
            .order_by(WorkoutModel.iso_week_start_date.asc(), WorkoutModel.id.asc())
            .all()
        )

    def _sleeps_in_range(self, start_week: date, end_week: date) -> list[SleepModel]:
        return (
            self.db.query(SleepModel)
            .filter(
                SleepModel.iso_week_start_date >= start_week,
                SleepModel.iso_week_start_date <= end_week,
            )
            .order_by(SleepModel.iso_week_start_date.asc(), SleepModel.id.asc())
            .all()
        )

    def _recoveries_in_range(self, start_week: date, end_week: date) -> list[RecoveryModel]:
        return (
            self.db.query(RecoveryModel)
            .filter(
                RecoveryModel.iso_week_start_date >= start_week,
                RecoveryModel.iso_week_start_date <= end_week,
            )
            .order_by(RecoveryModel.iso_week_start_date.asc(), RecoveryModel.id.asc())
            .all()
        )

    def _build_week_point(
        self,
        week_start: date,
        workouts: list[WorkoutModel],
        sleeps: list[SleepModel],
        recoveries: list[RecoveryModel],
    ) -> TrendWeeklyPoint:
        average_recovery_score = _average_decimal(
            recovery.recovery_score
            for recovery in recoveries
            if recovery.recovery_score is not None
        )
        average_daily_strain = _average_decimal(
            workout.strain for workout in workouts if workout.strain is not None
        )
        recovery_per_strain = None
        if average_recovery_score is not None and average_daily_strain not in (None, 0):
            recovery_per_strain = round(average_recovery_score / average_daily_strain, 4)

        return TrendWeeklyPoint(
            week_start_date=week_start,
            week_end_date=week_start + timedelta(days=6),
            workout_count=len(workouts),
            sleep_count=len(sleeps),
            recovery_count=len(recoveries),
            average_recovery_score=average_recovery_score,
            average_daily_strain=average_daily_strain,
            recovery_per_strain=recovery_per_strain,
        )

    def _build_comparison_card(
        self,
        *,
        metric: str,
        label: str,
        series: list[float | None],
        current_points: list[TrendWeeklyPoint],
        previous_points: list[TrendWeeklyPoint],
    ) -> RollingComparisonCard:
        current_average = _average_values(series[-ROLLING_WINDOW_WEEKS:])
        previous_average = _average_values(
            series[-ROLLING_WINDOW_WEEKS * 2 : -ROLLING_WINDOW_WEEKS]
        )
        delta = None
        direction = "insufficient"
        has_enough_history = current_average is not None and previous_average is not None
        if has_enough_history:
            delta = round(current_average - previous_average, 2)
            direction = "flat"
            if delta > 0.01:
                direction = "up"
            elif delta < -0.01:
                direction = "down"

        return RollingComparisonCard(
            metric=metric,  # type: ignore[arg-type]
            label=label,
            current_window_start_date=current_points[0].week_start_date,
            current_window_end_date=current_points[-1].week_end_date,
            previous_window_start_date=previous_points[0].week_start_date,
            previous_window_end_date=previous_points[-1].week_end_date,
            current_average=current_average,
            previous_average=previous_average,
            delta=delta,
            direction=direction,  # type: ignore[arg-type]
            has_enough_history=has_enough_history,
        )

    def _interpretation(
        self,
        weekly_series: list[TrendWeeklyPoint],
        comparison_cards: list[RollingComparisonCard],
    ) -> tuple[str, str]:
        recovery_card = next(card for card in comparison_cards if card.metric == "recovery")
        strain_card = next(card for card in comparison_cards if card.metric == "strain")
        if all(
            point.recovery_count == 0
            and point.workout_count == 0
            and point.sleep_count == 0
            for point in weekly_series
        ):
            return (
                "Not enough WHOOP history yet to read a trend.",
                "empty",
            )
        if not recovery_card.has_enough_history or not strain_card.has_enough_history:
            return (
                (
                    "There is some recent history, but the four-week comparison is still "
                    "too sparse to call a trend."
                ),
                "partial",
            )

        recovery_delta = recovery_card.delta or 0
        strain_delta = strain_card.delta or 0
        if recovery_delta > 0 and strain_delta <= 0:
            return (
                "Recovery is moving up while strain is steady or easing.",
                "ready",
            )
        if recovery_delta > 0 and strain_delta > 0:
            return (
                "Recovery is holding up even as strain rises. Keep the ramp measured.",
                "ready",
            )
        if recovery_delta < 0 and strain_delta > 0:
            return (
                "Strain is rising while recovery softens. Ease the next block if this persists.",
                "ready",
            )
        if recovery_delta < 0 and strain_delta <= 0:
            return (
                (
                    "Recovery is easing while strain is not climbing. "
                    "Watch the next few weeks closely."
                ),
                "ready",
            )
        return (
            "Recovery and strain are steady across the last four weeks.",
            "ready",
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


def _average_values(values: Iterable[float | None]) -> float | None:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return round(sum(numeric_values) / len(numeric_values), 2)
