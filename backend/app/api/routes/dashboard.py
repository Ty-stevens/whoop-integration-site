from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.core.time import iso_week_start
from app.schemas.dashboard import CurrentWeekDashboardResponse
from app.services.metrics.current_week import CurrentWeekMetricsService
from app.services.metrics.types import MetricsError

router = APIRouter()
WeekStartQuery = Annotated[date | None, Query()]


@router.get("/current-week", response_model=CurrentWeekDashboardResponse)
def current_week_dashboard(
    db: DbSession,
    week_start_date: WeekStartQuery = None,
) -> CurrentWeekDashboardResponse:
    requested_week = week_start_date or iso_week_start(date.today())
    try:
        return CurrentWeekMetricsService(db).build(requested_week)
    except MetricsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
