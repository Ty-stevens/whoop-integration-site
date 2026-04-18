from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal


@dataclass(frozen=True)
class ZoneProgress:
    zone: int
    actual_seconds: int
    actual_minutes: int
    target_minutes: int
    percent_complete: float | None
    remaining_minutes: int
    exceeded: bool


@dataclass(frozen=True)
class SessionProgress:
    completed: int
    target: int
    remaining: int
    percent_complete: float | None


@dataclass(frozen=True)
class CurrentWeekSummary:
    week_start_date: date
    week_end_date: date
    has_goal_profile: bool
    goal_profile_id: int | None
    last_successful_sync_at_utc: datetime | None
    zones: list[ZoneProgress]
    cardio_sessions: SessionProgress
    strength_sessions: SessionProgress
    total_training_seconds: int
    average_recovery_score: float | None
    average_daily_strain: float | None


class MetricsError(ValueError):
    pass


@dataclass(frozen=True)
class TrendWeeklyPoint:
    week_start_date: date
    week_end_date: date
    workout_count: int
    sleep_count: int
    recovery_count: int
    average_recovery_score: float | None
    average_daily_strain: float | None
    recovery_per_strain: float | None


@dataclass(frozen=True)
class RollingComparisonCard:
    metric: Literal["recovery", "strain"]
    label: str
    current_window_start_date: date
    current_window_end_date: date
    previous_window_start_date: date
    previous_window_end_date: date
    current_average: float | None
    previous_average: float | None
    delta: float | None
    direction: Literal["up", "down", "flat", "insufficient"]
    has_enough_history: bool


@dataclass(frozen=True)
class RecoveryStrainTrendsSummary:
    range_start_week: date
    range_end_week: date
    weekly_series: list[TrendWeeklyPoint]
    comparison_cards: list[RollingComparisonCard]
    interpretation_text: str
    data_state: Literal["empty", "partial", "ready"]


@dataclass(frozen=True)
class MonthlyTrainingSummary:
    month_start_date: date
    month_end_date: date
    month_label: str
    workout_count: int
    sleep_count: int
    recovery_count: int
    training_seconds: int
    zone1_minutes: int
    zone2_minutes: int
    zone3_minutes: int
    zone4_minutes: int
    zone5_minutes: int
    cardio_count: int
    strength_count: int
    other_count: int
    unknown_count: int
    average_recovery_score: float | None
    average_daily_strain: float | None


@dataclass(frozen=True)
class ConsistencySummary:
    weeks_in_range: int
    active_weeks: int
    weeks_with_workouts: int
    weeks_with_sleeps: int
    weeks_with_recoveries: int
    training_week_coverage_percent: float | None
    sleep_week_coverage_percent: float | None
    recovery_week_coverage_percent: float | None
    summary_text: str


@dataclass(frozen=True)
class SixMonthReportSummary:
    range_start_date: date
    range_end_date: date
    month_count: int
    monthly_summaries: list[MonthlyTrainingSummary]
    consistency_summary: ConsistencySummary
