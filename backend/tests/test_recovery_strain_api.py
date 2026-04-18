from datetime import UTC, date, datetime, timedelta

from app.db.session import SessionLocal
from app.models.facts import RecoveryModel, SleepModel, WorkoutModel
from tests.fact_fixtures import recovery_values, sleep_values, workout_values


def create_workout(
    db,
    *,
    external_id: str,
    start_date: date,
    week_start: date,
    month_start: date,
    strain: float,
) -> WorkoutModel:
    values = workout_values(external_id=external_id, raw_payload_json={"id": external_id})
    values.update(
        {
            "start_time_utc": datetime.combine(start_date, datetime.min.time(), tzinfo=UTC),
            "end_time_utc": datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
            + timedelta(hours=1),
            "local_start_date": start_date,
            "iso_week_start_date": week_start,
            "local_month_start_date": month_start,
            "strain": strain,
        }
    )
    row = WorkoutModel(**values)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_sleep(
    db,
    *,
    external_id: str,
    start_date: date,
    week_start: date,
    month_start: date,
) -> SleepModel:
    values = sleep_values(external_id=external_id, payload_hash=f"{external_id}-hash")
    values.update(
        {
            "start_time_utc": datetime.combine(start_date, datetime.min.time(), tzinfo=UTC),
            "end_time_utc": datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
            + timedelta(hours=8),
            "local_start_date": start_date,
            "iso_week_start_date": week_start,
            "local_month_start_date": month_start,
        }
    )
    row = SleepModel(**values)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_recovery(
    db,
    *,
    cycle_id: str,
    local_date: date,
    week_start: date,
    month_start: date,
    recovery_score: float,
) -> RecoveryModel:
    values = recovery_values(cycle_id=cycle_id, payload_hash=f"{cycle_id}-hash")
    values.update(
        {
            "local_date": local_date,
            "iso_week_start_date": week_start,
            "local_month_start_date": month_start,
            "recovery_score": recovery_score,
        }
    )
    row = RecoveryModel(**values)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_recovery_strain_api_returns_series_and_cards(client):
    with SessionLocal() as db:
        for offset, week_start in enumerate(
            [
                date(2026, 2, 16),
                date(2026, 2, 23),
                date(2026, 3, 2),
                date(2026, 3, 9),
                date(2026, 3, 16),
                date(2026, 3, 23),
                date(2026, 3, 30),
                date(2026, 4, 6),
            ]
        ):
            create_sleep(
                db,
                external_id=f"sleep-{offset}",
                start_date=week_start + timedelta(days=1),
                week_start=week_start,
                month_start=date(week_start.year, week_start.month, 1),
            )
            create_recovery(
                db,
                cycle_id=f"cycle-{offset}",
                local_date=week_start + timedelta(days=1),
                week_start=week_start,
                month_start=date(week_start.year, week_start.month, 1),
                recovery_score=60 + offset * 3,
            )
            create_workout(
                db,
                external_id=f"workout-{offset}",
                start_date=week_start + timedelta(days=2),
                week_start=week_start,
                month_start=date(week_start.year, week_start.month, 1),
                strain=8 - offset * 0.25,
            )

    response = client.get("/api/v1/recovery-strain/trends?as_of_date=2026-04-17")

    assert response.status_code == 200
    payload = response.json()
    assert payload["range_start_week"] == "2026-01-26"
    assert payload["range_end_week"] == "2026-04-13"
    assert len(payload["weekly_series"]) == 12
    assert payload["data_state"] == "ready"
    recovery_card = next(
        card for card in payload["comparison_cards"] if card["metric"] == "recovery"
    )
    strain_card = next(
        card for card in payload["comparison_cards"] if card["metric"] == "strain"
    )
    assert recovery_card["direction"] == "up"
    assert strain_card["direction"] == "down"
    assert payload["interpretation_text"] == (
        "Recovery is moving up while strain is steady or easing."
    )


def test_recovery_strain_api_handles_empty_history(client):
    response = client.get("/api/v1/recovery-strain/trends?as_of_date=2026-04-17")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_state"] == "empty"
    assert all(point["workout_count"] == 0 for point in payload["weekly_series"])
    assert all(card["direction"] == "insufficient" for card in payload["comparison_cards"])
    assert "not enough" in payload["interpretation_text"].lower()
