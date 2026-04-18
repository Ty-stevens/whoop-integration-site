from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.models.facts import WorkoutModel
from app.models.overlays import WorkoutAnnotationModel
from app.repositories.annotations import AnnotationRepository
from app.schemas.workouts import (
    RecentWorkoutsResponse,
    StrengthOverviewResponse,
    WorkoutAnnotationResponse,
    WorkoutAnnotationUpdate,
    WorkoutSummaryResponse,
)
from app.services.metrics.strength_overview import StrengthOverviewService

router = APIRouter()
LimitQuery = Annotated[int, Query(ge=1, le=365)]


@router.get("/recent", response_model=RecentWorkoutsResponse)
def recent_workouts(db: DbSession, limit: LimitQuery = 25) -> RecentWorkoutsResponse:
    rows = (
        db.query(WorkoutModel, WorkoutAnnotationModel)
        .outerjoin(WorkoutAnnotationModel, WorkoutAnnotationModel.workout_id == WorkoutModel.id)
        .order_by(WorkoutModel.start_time_utc.desc(), WorkoutModel.id.desc())
        .limit(limit)
        .all()
    )
    return RecentWorkoutsResponse(
        workouts=[_workout_response(workout, annotation) for workout, annotation in rows]
    )


@router.get("/strength-overview", response_model=StrengthOverviewResponse)
def strength_overview(db: DbSession, limit: LimitQuery = 180) -> StrengthOverviewResponse:
    return StrengthOverviewService(db).build(recent_limit=limit)


@router.patch("/{workout_id}/annotation", response_model=WorkoutAnnotationResponse)
def update_workout_annotation(
    workout_id: int,
    payload: WorkoutAnnotationUpdate,
    db: DbSession,
) -> WorkoutAnnotationResponse:
    workout = db.get(WorkoutModel, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")

    annotation = AnnotationRepository(db).upsert_workout_annotation(
        workout_id,
        manual_classification=payload.manual_classification,
        manual_strength_split=payload.manual_strength_split,
        tag=payload.tag,
        notes=payload.notes,
    )
    return WorkoutAnnotationResponse.model_validate(annotation)


def _workout_response(
    workout: WorkoutModel,
    annotation: WorkoutAnnotationModel | None,
) -> WorkoutSummaryResponse:
    manual_classification = annotation.manual_classification if annotation is not None else None
    return WorkoutSummaryResponse(
        id=workout.id,
        local_start_date=workout.local_start_date,
        start_time_utc=workout.start_time_utc,
        sport_name=workout.sport_name,
        score_state=workout.score_state,
        classification=workout.classification,
        effective_classification=manual_classification or workout.classification,
        duration_seconds=workout.duration_seconds,
        strain=float(workout.strain) if workout.strain is not None else None,
        average_hr=workout.average_hr,
        max_hr=workout.max_hr,
        zone1_seconds=workout.zone1_seconds,
        zone2_seconds=workout.zone2_seconds,
        zone3_seconds=workout.zone3_seconds,
        zone4_seconds=workout.zone4_seconds,
        zone5_seconds=workout.zone5_seconds,
        annotation=WorkoutAnnotationResponse.model_validate(annotation)
        if annotation is not None
        else None,
    )
