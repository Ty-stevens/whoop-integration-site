from datetime import date

import pytest
from pydantic import ValidationError

from app.db.session import SessionLocal
from app.jobs import seed
from app.models.overlays import GoalProfileModel
from app.repositories.goals import GoalRepository
from app.schemas.goals import GoalProfileCreate
from app.services.goal_service import GoalProfileError, GoalProfileService, seed_default_goals


def goal_payload(
    *,
    effective_from_date: date,
    effective_to_date: date | None = None,
    zone2_target_minutes: int = 150,
    created_reason: str = "test goal",
) -> GoalProfileCreate:
    return GoalProfileCreate(
        effective_from_date=effective_from_date,
        effective_to_date=effective_to_date,
        zone1_target_minutes=0,
        zone2_target_minutes=zone2_target_minutes,
        zone3_target_minutes=0,
        zone4_target_minutes=0,
        zone5_target_minutes=0,
        cardio_sessions_target=3,
        strength_sessions_target=2,
        created_reason=created_reason,
    )


def test_creating_future_profile_closes_previous_open_profile():
    with SessionLocal() as db:
        service = GoalProfileService(db)
        first = service.create_profile(
            goal_payload(effective_from_date=date(2026, 4, 6), zone2_target_minutes=150)
        )
        second = service.create_profile(
            goal_payload(effective_from_date=date(2026, 4, 13), zone2_target_minutes=175)
        )
        db.refresh(first)

    assert first.effective_to_date == date(2026, 4, 12)
    assert second.effective_to_date is None


def test_historical_closed_profile_remains_unchanged_when_new_profile_is_created():
    with SessionLocal() as db:
        repo = GoalRepository(db)
        historical = repo.create(
            goal_payload(
                effective_from_date=date(2026, 3, 30),
                effective_to_date=date(2026, 4, 5),
                zone2_target_minutes=120,
            ).model_dump()
        )
        service = GoalProfileService(db)
        service.create_profile(goal_payload(effective_from_date=date(2026, 4, 6)))
        db.refresh(historical)

    assert historical.effective_to_date == date(2026, 4, 5)


def test_overlapping_closed_profile_is_rejected():
    with SessionLocal() as db:
        repo = GoalRepository(db)
        repo.create(
            goal_payload(
                effective_from_date=date(2026, 4, 6),
                effective_to_date=date(2026, 4, 19),
            ).model_dump()
        )

        with pytest.raises(GoalProfileError, match="overlaps"):
            GoalProfileService(db).create_profile(
                goal_payload(effective_from_date=date(2026, 4, 13))
            )


def test_backfilled_open_profile_before_existing_open_profile_is_rejected():
    with SessionLocal() as db:
        service = GoalProfileService(db)
        service.create_profile(goal_payload(effective_from_date=date(2026, 4, 13)))

        with pytest.raises(GoalProfileError, match="overlaps"):
            service.create_profile(goal_payload(effective_from_date=date(2026, 4, 6)))


def test_backfilled_closed_profile_before_existing_open_profile_is_allowed():
    with SessionLocal() as db:
        service = GoalProfileService(db)
        active = service.create_profile(goal_payload(effective_from_date=date(2026, 4, 13)))
        historical = service.create_profile(
            goal_payload(
                effective_from_date=date(2026, 4, 6),
                effective_to_date=date(2026, 4, 12),
                zone2_target_minutes=125,
            )
        )
        db.refresh(active)

    assert active.effective_to_date is None
    assert historical.effective_to_date == date(2026, 4, 12)


def test_active_profile_resolution_returns_historical_truth():
    with SessionLocal() as db:
        service = GoalProfileService(db)
        service.create_profile(
            goal_payload(effective_from_date=date(2026, 4, 6), zone2_target_minutes=150)
        )
        service.create_profile(
            goal_payload(effective_from_date=date(2026, 4, 13), zone2_target_minutes=175)
        )

        first = service.active_for_week(date(2026, 4, 6))
        second = service.active_for_week(date(2026, 4, 13))

    assert first.zone2_target_minutes == 150
    assert second.zone2_target_minutes == 175


def test_non_monday_effective_from_is_rejected():
    with pytest.raises(ValidationError, match="Monday ISO week start"):
        goal_payload(effective_from_date=date(2026, 4, 7))


def test_negative_targets_are_rejected():
    with pytest.raises(ValidationError):
        GoalProfileCreate(
            effective_from_date=date(2026, 4, 6),
            zone1_target_minutes=-1,
        )


def test_default_seed_is_idempotent():
    with SessionLocal() as db:
        first = seed_default_goals(db, effective_from_date=date(2026, 4, 6))
        second = seed_default_goals(db, effective_from_date=date(2026, 4, 13))
        count = db.query(GoalProfileModel).count()

    assert first.id == second.id
    assert count == 1
    assert first.effective_from_date == date(2026, 4, 6)
    assert first.zone2_target_minutes == 150
    assert first.cardio_sessions_target == 3
    assert first.strength_sessions_target == 2


def test_seed_command_inserts_defaults_once(capsys):
    first_exit = seed.main(["--effective-from", "2026-04-06"])
    second_exit = seed.main(["--effective-from", "2026-04-13"])

    with SessionLocal() as db:
        profiles = GoalRepository(db).history()

    output = capsys.readouterr().out
    assert first_exit == 0
    assert second_exit == 0
    assert len(profiles) == 1
    assert profiles[0].effective_from_date == date(2026, 4, 6)
    assert "zone2=150" in output
