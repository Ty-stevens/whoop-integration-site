from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.time import iso_week_start
from app.models.overlays import GoalProfileModel
from app.repositories.goals import GoalRepository
from app.schemas.goals import GoalProfileCreate

DEFAULT_GOAL_REASON = "initial training default"


class GoalProfileError(ValueError):
    pass


class GoalProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = GoalRepository(db)

    def active_for_week(self, week_start_date: date) -> GoalProfileModel | None:
        self._validate_week_start(week_start_date)
        return self.repository.active_for_week(week_start_date)

    def active_for_current_week(self) -> GoalProfileModel | None:
        return self.repository.active_for_week(iso_week_start(date.today()))

    def history(self) -> list[GoalProfileModel]:
        return self.repository.history()

    def create_profile(self, payload: GoalProfileCreate) -> GoalProfileModel:
        self._validate_profile_dates(payload.effective_from_date, payload.effective_to_date)
        self._reject_closed_overlap(payload.effective_from_date, payload.effective_to_date)
        self._close_previous_open_profile(payload.effective_from_date)

        row = GoalProfileModel(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def seed_default(self, effective_from_date: date | None = None) -> GoalProfileModel:
        existing = self.repository.history()
        if existing:
            return existing[-1]

        start_date = effective_from_date or iso_week_start(date.today())
        payload = GoalProfileCreate(
            effective_from_date=start_date,
            zone1_target_minutes=0,
            zone2_target_minutes=150,
            zone3_target_minutes=0,
            zone4_target_minutes=0,
            zone5_target_minutes=0,
            cardio_sessions_target=3,
            strength_sessions_target=2,
            created_reason=DEFAULT_GOAL_REASON,
        )
        return self.create_profile(payload)

    def _close_previous_open_profile(self, effective_from_date: date) -> None:
        previous = (
            self.db.query(GoalProfileModel)
            .filter(
                GoalProfileModel.effective_from_date < effective_from_date,
                GoalProfileModel.effective_to_date.is_(None),
            )
            .order_by(GoalProfileModel.effective_from_date.desc())
            .first()
        )
        if previous is None:
            return
        previous.effective_to_date = effective_from_date - timedelta(days=1)

    def _reject_closed_overlap(
        self,
        effective_from_date: date,
        effective_to_date: date | None,
    ) -> None:
        incoming_to = effective_to_date or date.max
        overlap = (
            self.db.query(GoalProfileModel)
            .filter(
                GoalProfileModel.effective_to_date.is_not(None),
                GoalProfileModel.effective_from_date <= incoming_to,
                GoalProfileModel.effective_to_date >= effective_from_date,
            )
            .first()
        )
        if overlap is not None:
            raise GoalProfileError("Goal profile overlaps an existing historical profile")

        open_overlap = (
            self.db.query(GoalProfileModel)
            .filter(
                GoalProfileModel.effective_to_date.is_(None),
                GoalProfileModel.effective_from_date >= effective_from_date,
                GoalProfileModel.effective_from_date <= incoming_to,
            )
            .first()
        )
        if open_overlap is not None:
            raise GoalProfileError("Goal profile overlaps an existing active profile")

    def _validate_profile_dates(
        self,
        effective_from_date: date,
        effective_to_date: date | None,
    ) -> None:
        self._validate_week_start(effective_from_date)
        if effective_to_date is not None and effective_to_date < effective_from_date:
            raise GoalProfileError("effective_to_date cannot be before effective_from_date")

    def _validate_week_start(self, week_start_date: date) -> None:
        if week_start_date.weekday() != 0:
            raise GoalProfileError("Date must be a Monday ISO week start")


def seed_default_goals(db: Session, effective_from_date: date | None = None) -> GoalProfileModel:
    return GoalProfileService(db).seed_default(effective_from_date)
