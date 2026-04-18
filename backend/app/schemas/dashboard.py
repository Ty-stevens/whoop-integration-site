from datetime import date, datetime

from pydantic import BaseModel


class ZoneProgressResponse(BaseModel):
    zone: int
    actual_seconds: int
    actual_minutes: int
    target_minutes: int
    percent_complete: float | None
    remaining_minutes: int
    exceeded: bool


class SessionProgressResponse(BaseModel):
    completed: int
    target: int
    remaining: int
    percent_complete: float | None


class CurrentWeekDashboardResponse(BaseModel):
    week_start_date: date
    week_end_date: date
    has_goal_profile: bool
    goal_profile_id: int | None
    last_successful_sync_at_utc: datetime | None
    zones: list[ZoneProgressResponse]
    cardio_sessions: SessionProgressResponse
    strength_sessions: SessionProgressResponse
    total_training_seconds: int
    average_recovery_score: float | None
    average_daily_strain: float | None

    model_config = {"from_attributes": True}
