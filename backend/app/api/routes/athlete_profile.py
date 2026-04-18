from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.athlete_profile import AthleteProfile, AthleteProfileResponse
from app.services.athlete_profile_service import get_athlete_profile, upsert_athlete_profile

router = APIRouter()


@router.get("", response_model=AthleteProfileResponse)
def read_athlete_profile(db: DbSession) -> AthleteProfileResponse:
    return get_athlete_profile(db)


@router.put("", response_model=AthleteProfileResponse)
def update_athlete_profile(
    payload: AthleteProfile,
    db: DbSession,
) -> AthleteProfileResponse:
    return upsert_athlete_profile(db, payload)
