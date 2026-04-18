from datetime import date
from typing import Literal

from pydantic import BaseModel


class TrendWeeklyPointResponse(BaseModel):
    week_start_date: date
    week_end_date: date
    workout_count: int
    sleep_count: int
    recovery_count: int
    average_recovery_score: float | None
    average_daily_strain: float | None
    recovery_per_strain: float | None


class RollingComparisonCardResponse(BaseModel):
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


class RecoveryStrainTrendsResponse(BaseModel):
    range_start_week: date
    range_end_week: date
    weekly_series: list[TrendWeeklyPointResponse]
    comparison_cards: list[RollingComparisonCardResponse]
    interpretation_text: str
    data_state: Literal["empty", "partial", "ready"]

    model_config = {"from_attributes": True}
