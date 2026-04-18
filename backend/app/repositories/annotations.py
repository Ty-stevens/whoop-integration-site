from sqlalchemy.orm import Session

from app.models.overlays import WorkoutAnnotationModel


class AnnotationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_workout_annotation(
        self,
        workout_id: int,
        *,
        manual_classification: str | None = None,
        manual_strength_split: str | None = None,
        tag: str | None = None,
        notes: str | None = None,
    ) -> WorkoutAnnotationModel:
        row = (
            self.db.query(WorkoutAnnotationModel)
            .filter(WorkoutAnnotationModel.workout_id == workout_id)
            .one_or_none()
        )
        if row is None:
            row = WorkoutAnnotationModel(workout_id=workout_id)
            self.db.add(row)
        row.manual_classification = manual_classification
        row.manual_strength_split = manual_strength_split
        row.tag = tag
        row.notes = notes
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_for_workout(self, workout_id: int) -> WorkoutAnnotationModel | None:
        return (
            self.db.query(WorkoutAnnotationModel)
            .filter(WorkoutAnnotationModel.workout_id == workout_id)
            .one_or_none()
        )

