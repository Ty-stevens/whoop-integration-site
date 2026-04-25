from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.goals import GoalProfileResponse


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


BenchmarkMetric = Literal[
    "zone1_target_minutes",
    "zone2_target_minutes",
    "zone3_target_minutes",
    "zone4_target_minutes",
    "zone5_target_minutes",
    "cardio_sessions_target",
    "strength_sessions_target",
]


class AiBenchmarkUpdateRequest(BaseModel):
    apply: bool = False
    effective_from_date: date | None = None


class AiBenchmarkTargets(BaseModel):
    zone1_target_minutes: int = Field(ge=0, le=3000)
    zone2_target_minutes: int = Field(ge=0, le=3000)
    zone3_target_minutes: int = Field(ge=0, le=3000)
    zone4_target_minutes: int = Field(ge=0, le=3000)
    zone5_target_minutes: int = Field(ge=0, le=3000)
    cardio_sessions_target: int = Field(ge=0, le=21)
    strength_sessions_target: int = Field(ge=0, le=21)


class AiBenchmarkSourceRef(BaseModel):
    source_type: str = Field(max_length=80)
    date: str | None = Field(default=None, max_length=40)
    metric: str = Field(max_length=80)
    value: str | float | int | None = None


class AiBenchmarkChange(BaseModel):
    metric: BenchmarkMetric
    current_value: int
    recommended_value: int
    reason: str = Field(max_length=500)
    sources: list[AiBenchmarkSourceRef] = []


class AiBenchmarkProposal(BaseModel):
    targets: AiBenchmarkTargets
    summary: str = Field(max_length=1000)
    confidence: Literal["low", "medium", "high"] = "medium"
    changes: list[AiBenchmarkChange] = []


class AiBenchmarkUpdateResponse(BaseModel):
    status: Literal["disabled", "setup_error", "success", "error"]
    applied: bool = False
    proposal: AiBenchmarkProposal | None = None
    profile: GoalProfileResponse | None = None
    generated_at_utc: datetime
    message: str
