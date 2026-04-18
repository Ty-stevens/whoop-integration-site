from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.schemas.goals import (
    ActiveGoalProfileResponse,
    GoalProfileCreate,
    GoalProfileListResponse,
    GoalProfileResponse,
)
from app.services.goal_service import GoalProfileError, GoalProfileService

router = APIRouter()
WeekStartQuery = Annotated[date, Query()]


@router.get("/active", response_model=ActiveGoalProfileResponse)
def active_goal_profile(db: DbSession) -> ActiveGoalProfileResponse:
    profile = GoalProfileService(db).active_for_current_week()
    if profile is None:
        return ActiveGoalProfileResponse(message="No active goal profile exists yet.")
    return ActiveGoalProfileResponse(profile=profile, message="Active goal profile found.")


@router.get("/for-week", response_model=ActiveGoalProfileResponse)
def goal_profile_for_week(
    db: DbSession,
    week_start_date: WeekStartQuery,
) -> ActiveGoalProfileResponse:
    try:
        profile = GoalProfileService(db).active_for_week(week_start_date)
    except GoalProfileError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if profile is None:
        return ActiveGoalProfileResponse(message="No goal profile exists for this week.")
    return ActiveGoalProfileResponse(profile=profile, message="Goal profile found for week.")


@router.get("/history", response_model=GoalProfileListResponse)
def goal_profile_history(db: DbSession) -> GoalProfileListResponse:
    return GoalProfileListResponse(profiles=GoalProfileService(db).history())


@router.post("/", response_model=GoalProfileResponse)
def create_goal_profile(payload: GoalProfileCreate, db: DbSession) -> GoalProfileResponse:
    try:
        return GoalProfileService(db).create_profile(payload)
    except GoalProfileError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
