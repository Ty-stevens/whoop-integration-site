from dataclasses import asdict
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.recovery_strain import RecoveryStrainTrendsResponse
from app.services.metrics.recovery_strain import RecoveryStrainMetricsService

router = APIRouter()
AsOfDateQuery = Annotated[date | None, Query()]


@router.get("/trends", response_model=RecoveryStrainTrendsResponse)
def recovery_strain_trends(
    db: DbSession,
    as_of_date: AsOfDateQuery = None,
) -> RecoveryStrainTrendsResponse:
    summary = RecoveryStrainMetricsService(db).build(as_of_date or date.today())
    return RecoveryStrainTrendsResponse.model_validate(asdict(summary))
