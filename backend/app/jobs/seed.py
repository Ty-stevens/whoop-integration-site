import argparse
from collections.abc import Sequence
from datetime import date

from app.db.session import SessionLocal
from app.services.goal_service import seed_default_goals


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed EnduraSync local defaults.")
    parser.add_argument("--effective-from", type=date.fromisoformat, default=None)
    args = parser.parse_args(argv)

    with SessionLocal() as db:
        profile = seed_default_goals(db, effective_from_date=args.effective_from)

    print(
        "Goal defaults ready: "
        f"id={profile.id} effective_from={profile.effective_from_date.isoformat()} "
        f"zone2={profile.zone2_target_minutes} cardio={profile.cardio_sessions_target} "
        f"strength={profile.strength_sessions_target}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
