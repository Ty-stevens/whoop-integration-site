from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AiStatusResponse(BaseModel):
    status: Literal["disabled", "configured", "reachable", "failing"]
    provider: Literal["disabled", "openai_compatible", "openclaw"]
    enabled: bool
    model: str | None
    message: str


class AiWeeklySummaryResponse(BaseModel):
    status: Literal["disabled", "success", "error"]
    summary: str | None = None
    observations: list[str] = []
    generated_at_utc: datetime
    message: str


class AiGoalSuggestion(BaseModel):
    zone1_target_minutes: int
    zone2_target_minutes: int
    zone3_target_minutes: int
    zone4_target_minutes: int
    zone5_target_minutes: int
    cardio_sessions_target: int
    strength_sessions_target: int
    rationale: str
    confidence: str


class AiGoalSuggestionsResponse(BaseModel):
    status: Literal["disabled", "success", "error"]
    suggestions: list[AiGoalSuggestion] = []
    generated_at_utc: datetime
    message: str
