from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Classification = Literal["cardio", "strength", "other", "unknown"]
StrengthSplit = Literal["upper", "lower", "full", "unknown"]


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class WorkoutAnnotationResponse(BaseModel):
    manual_classification: Classification | None = None
    manual_strength_split: StrengthSplit | None = None
    tag: str | None = None
    notes: str | None = None
    updated_at_utc: datetime | None = None

    model_config = {"from_attributes": True}


class WorkoutAnnotationUpdate(BaseModel):
    manual_classification: Classification | None = None
    manual_strength_split: StrengthSplit | None = None
    tag: str | None = Field(default=None, max_length=120)
    notes: str | None = None

    @field_validator("tag", "notes", mode="before")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return _blank_to_none(value)


class WorkoutSummaryResponse(BaseModel):
    id: int
    local_start_date: date
    start_time_utc: datetime
    sport_name: str | None
    score_state: str | None
    classification: Classification
    effective_classification: Classification
    duration_seconds: int
    strain: float | None
    average_hr: int | None
    max_hr: int | None
    zone1_seconds: int
    zone2_seconds: int
    zone3_seconds: int
    zone4_seconds: int
    zone5_seconds: int
    annotation: WorkoutAnnotationResponse | None = None


class RecentWorkoutsResponse(BaseModel):
    workouts: list[WorkoutSummaryResponse]


class StrengthSplitCountResponse(BaseModel):
    split: Literal["upper", "lower", "full", "unknown", "untagged"]
    count: int


class StrengthPeriodCountResponse(BaseModel):
    period_start_date: date
    label: str
    count: int


class StrengthOverviewResponse(BaseModel):
    range_start_date: date
    range_end_date: date
    strength_sessions: int
    strength_strain: float | None
    split_counts: list[StrengthSplitCountResponse]
    weekly_counts: list[StrengthPeriodCountResponse]
    monthly_counts: list[StrengthPeriodCountResponse]
    untagged_sessions: int
