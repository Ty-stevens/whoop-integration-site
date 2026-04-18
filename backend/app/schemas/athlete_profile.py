from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AthleteProfile(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    gender: str | None = Field(default=None, max_length=80)
    date_of_birth: date | None = None
    age_years: int | None = Field(default=None, ge=13, le=120)
    height_cm: float | None = Field(default=None, ge=80, le=260)
    weight_kg: float | None = Field(default=None, ge=25, le=350)
    training_focus: str | None = Field(default=None, max_length=500)
    experience_level: Literal["beginner", "intermediate", "advanced", "elite"] | None = None
    notes_for_ai: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_age_source(self) -> "AthleteProfile":
        if self.date_of_birth is not None and self.age_years is not None:
            raise ValueError("Provide either date_of_birth or age_years, not both")
        return self


class AthleteProfileResponse(AthleteProfile):
    ai_context_allowed: bool = False

