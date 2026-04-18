from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.overlays import GoalProfileModel


class GoalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, values: dict) -> GoalProfileModel:
        row = GoalProfileModel(**values)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def active_for_week(self, week_start: date) -> GoalProfileModel | None:
        return (
            self.db.query(GoalProfileModel)
            .filter(
                GoalProfileModel.effective_from_date <= week_start,
                or_(
                    GoalProfileModel.effective_to_date.is_(None),
                    GoalProfileModel.effective_to_date >= week_start,
                ),
            )
            .order_by(GoalProfileModel.effective_from_date.desc())
            .first()
        )

    def history(self) -> list[GoalProfileModel]:
        return (
            self.db.query(GoalProfileModel)
            .order_by(GoalProfileModel.effective_from_date.desc())
            .all()
        )

