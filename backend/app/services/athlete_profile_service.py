from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.athlete_profile import AthleteProfileModel
from app.schemas.athlete_profile import AthleteProfile, AthleteProfileResponse

ATHLETE_PROFILE_ROW_ID = 1


def _to_response(row: AthleteProfileModel | None) -> AthleteProfileResponse:
    payload = {}
    if row is not None:
        payload = {
            "display_name": row.display_name,
            "gender": row.gender,
            "date_of_birth": row.date_of_birth,
            "age_years": row.age_years,
            "height_cm": row.height_cm,
            "weight_kg": row.weight_kg,
            "training_focus": row.training_focus,
            "experience_level": row.experience_level,
            "notes_for_ai": row.notes_for_ai,
        }
    return AthleteProfileResponse(
        **payload,
        ai_context_allowed=get_settings().ai_enabled,
    )


def get_athlete_profile(db: Session) -> AthleteProfileResponse:
    return _to_response(db.get(AthleteProfileModel, ATHLETE_PROFILE_ROW_ID))


def upsert_athlete_profile(db: Session, payload: AthleteProfile) -> AthleteProfileResponse:
    row = db.get(AthleteProfileModel, ATHLETE_PROFILE_ROW_ID)
    if row is None:
        row = AthleteProfileModel(id=ATHLETE_PROFILE_ROW_ID)
        db.add(row)

    row.display_name = payload.display_name
    row.gender = payload.gender
    row.date_of_birth = payload.date_of_birth
    row.age_years = payload.age_years
    row.height_cm = payload.height_cm
    row.weight_kg = payload.weight_kg
    row.training_focus = payload.training_focus
    row.experience_level = payload.experience_level
    row.notes_for_ai = payload.notes_for_ai
    row.updated_at_utc = datetime.now(UTC)
    db.commit()
    db.refresh(row)
    return _to_response(row)

