from datetime import date

from pydantic import BaseModel


class MonthlyTrainingSummaryResponse(BaseModel):
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


class ConsistencySummaryResponse(BaseModel):
    weeks_in_range: int
    active_weeks: int
    weeks_with_workouts: int
    weeks_with_sleeps: int
    weeks_with_recoveries: int
    training_week_coverage_percent: float | None
    sleep_week_coverage_percent: float | None
    recovery_week_coverage_percent: float | None
    summary_text: str


class SixMonthReportResponse(BaseModel):
    range_start_date: date
    range_end_date: date
    month_count: int
    monthly_summaries: list[MonthlyTrainingSummaryResponse]
    consistency_summary: ConsistencySummaryResponse

    model_config = {"from_attributes": True}
