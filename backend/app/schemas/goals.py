from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class GoalProfileBase(BaseModel):
    effective_from_date: date
    effective_to_date: date | None = None
    zone1_target_minutes: int = Field(ge=0, default=0)
    zone2_target_minutes: int = Field(ge=0, default=150)
    zone3_target_minutes: int = Field(ge=0, default=0)
    zone4_target_minutes: int = Field(ge=0, default=0)
    zone5_target_minutes: int = Field(ge=0, default=0)
    cardio_sessions_target: int = Field(ge=0, default=3)
    strength_sessions_target: int = Field(ge=0, default=2)
    created_reason: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def validate_dates(self) -> "GoalProfileBase":
        if self.effective_from_date.weekday() != 0:
            raise ValueError("effective_from_date must be a Monday ISO week start")
        if (
            self.effective_to_date is not None
            and self.effective_to_date < self.effective_from_date
        ):
            raise ValueError("effective_to_date cannot be before effective_from_date")
        return self


class GoalProfileCreate(GoalProfileBase):
    pass


class GoalProfileResponse(GoalProfileBase):
    id: int
    created_at_utc: datetime

    model_config = {"from_attributes": True}


class GoalProfileListResponse(BaseModel):
    profiles: list[GoalProfileResponse]


class ActiveGoalProfileResponse(BaseModel):
    profile: GoalProfileResponse | None = None
    message: str
