from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.facts import WorkoutModel
from app.models.overlays import WorkoutAnnotationModel
from app.schemas.workouts import (
    StrengthOverviewResponse,
    StrengthPeriodCountResponse,
    StrengthSplitCountResponse,
)


class StrengthOverviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, *, recent_limit: int = 180) -> StrengthOverviewResponse:
        rows = (
            self.db.query(WorkoutModel, WorkoutAnnotationModel)
            .outerjoin(WorkoutAnnotationModel, WorkoutAnnotationModel.workout_id == WorkoutModel.id)
            .order_by(WorkoutModel.start_time_utc.desc(), WorkoutModel.id.desc())
            .limit(recent_limit)
            .all()
        )
        workouts = [
            (workout, annotation)
            for workout, annotation in rows
            if (annotation.manual_classification if annotation else None) == "strength"
            or (
                annotation is None or annotation.manual_classification is None
            )
            and workout.classification == "strength"
        ]

        today = date.today()
        range_start = min((workout.local_start_date for workout, _ in workouts), default=today)
        range_end = max((workout.local_start_date for workout, _ in workouts), default=today)
        split_counts = {"upper": 0, "lower": 0, "full": 0, "unknown": 0, "untagged": 0}
        weekly_counts: dict[date, int] = {}
        monthly_counts: dict[date, int] = {}
        strain_values: list[Decimal] = []

        for workout, annotation in workouts:
            if workout.strain is not None:
                strain_values.append(Decimal(workout.strain))
            split = annotation.manual_strength_split if annotation else None
            split_counts[split or "untagged"] += 1
            weekly_counts[workout.iso_week_start_date] = (
                weekly_counts.get(workout.iso_week_start_date, 0) + 1
            )
            monthly_counts[workout.local_month_start_date] = (
                monthly_counts.get(workout.local_month_start_date, 0) + 1
            )

        return StrengthOverviewResponse(
            range_start_date=range_start,
            range_end_date=range_end,
            strength_sessions=len(workouts),
            strength_strain=round(float(sum(strain_values)), 2) if strain_values else None,
            split_counts=[
                StrengthSplitCountResponse(split=split, count=count)
                for split, count in split_counts.items()
            ],
            weekly_counts=[
                StrengthPeriodCountResponse(
                    period_start_date=period,
                    label=f"Week of {period.isoformat()}",
                    count=count,
                )
                for period, count in sorted(weekly_counts.items())
            ],
            monthly_counts=[
                StrengthPeriodCountResponse(
                    period_start_date=period,
                    label=period.strftime("%b %Y"),
                    count=count,
                )
                for period, count in sorted(monthly_counts.items())
            ],
            untagged_sessions=split_counts["untagged"],
        )
