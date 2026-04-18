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
    classification: str,
    strain: float,
    zone2_seconds: int,
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
            "classification": classification,
            "strain": strain,
            "zone2_seconds": zone2_seconds,
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


def seed_report_data(db):
    create_sleep(
        db,
        external_id="sleep-1",
        start_date=date(2025, 11, 4),
        week_start=date(2025, 11, 3),
        month_start=date(2025, 11, 1),
    )
    create_recovery(
        db,
        cycle_id="cycle-1",
        local_date=date(2025, 11, 4),
        week_start=date(2025, 11, 3),
        month_start=date(2025, 11, 1),
        recovery_score=70,
    )
    create_workout(
        db,
        external_id="workout-1",
        start_date=date(2025, 11, 5),
        week_start=date(2025, 11, 3),
        month_start=date(2025, 11, 1),
        classification="cardio",
        strain=7.5,
        zone2_seconds=1200,
    )

    create_sleep(
        db,
        external_id="sleep-2",
        start_date=date(2025, 12, 9),
        week_start=date(2025, 12, 8),
        month_start=date(2025, 12, 1),
    )
    create_recovery(
        db,
        cycle_id="cycle-2",
        local_date=date(2025, 12, 9),
        week_start=date(2025, 12, 8),
        month_start=date(2025, 12, 1),
        recovery_score=74,
    )
    create_workout(
        db,
        external_id="workout-2",
        start_date=date(2025, 12, 10),
        week_start=date(2025, 12, 8),
        month_start=date(2025, 12, 1),
        classification="strength",
        strain=8.0,
        zone2_seconds=1800,
    )

    create_sleep(
        db,
        external_id="sleep-3",
        start_date=date(2026, 1, 6),
        week_start=date(2026, 1, 5),
        month_start=date(2026, 1, 1),
    )
    create_recovery(
        db,
        cycle_id="cycle-3",
        local_date=date(2026, 1, 6),
        week_start=date(2026, 1, 5),
        month_start=date(2026, 1, 1),
        recovery_score=76,
    )
    create_workout(
        db,
        external_id="workout-3",
        start_date=date(2026, 1, 7),
        week_start=date(2026, 1, 5),
        month_start=date(2026, 1, 1),
        classification="other",
        strain=6.5,
        zone2_seconds=900,
    )

    create_sleep(
        db,
        external_id="sleep-4",
        start_date=date(2026, 2, 10),
        week_start=date(2026, 2, 9),
        month_start=date(2026, 2, 1),
    )
    create_recovery(
        db,
        cycle_id="cycle-4",
        local_date=date(2026, 2, 10),
        week_start=date(2026, 2, 9),
        month_start=date(2026, 2, 1),
        recovery_score=78,
    )
    create_workout(
        db,
        external_id="workout-4",
        start_date=date(2026, 2, 11),
        week_start=date(2026, 2, 9),
        month_start=date(2026, 2, 1),
        classification="unknown",
        strain=5.5,
        zone2_seconds=600,
    )

    create_sleep(
        db,
        external_id="sleep-5",
        start_date=date(2026, 3, 17),
        week_start=date(2026, 3, 16),
        month_start=date(2026, 3, 1),
    )
    create_recovery(
        db,
        cycle_id="cycle-5",
        local_date=date(2026, 3, 17),
        week_start=date(2026, 3, 16),
        month_start=date(2026, 3, 1),
        recovery_score=80,
    )
    create_workout(
        db,
        external_id="workout-5",
        start_date=date(2026, 3, 18),
        week_start=date(2026, 3, 16),
        month_start=date(2026, 3, 1),
        classification="cardio",
        strain=9.0,
        zone2_seconds=1500,
    )
    create_workout(
        db,
        external_id="workout-6",
        start_date=date(2026, 3, 19),
        week_start=date(2026, 3, 16),
        month_start=date(2026, 3, 1),
        classification="cardio",
        strain=9.5,
        zone2_seconds=600,
    )

    create_sleep(
        db,
        external_id="sleep-6",
        start_date=date(2026, 4, 7),
        week_start=date(2026, 4, 6),
        month_start=date(2026, 4, 1),
    )
    create_recovery(
        db,
        cycle_id="cycle-6",
        local_date=date(2026, 4, 7),
        week_start=date(2026, 4, 6),
        month_start=date(2026, 4, 1),
        recovery_score=82,
    )
    create_workout(
        db,
        external_id="workout-7",
        start_date=date(2026, 4, 8),
        week_start=date(2026, 4, 6),
        month_start=date(2026, 4, 1),
        classification="cardio",
        strain=10.0,
        zone2_seconds=1800,
    )


def test_six_month_report_api_returns_expected_shape_and_aggregation(client):
    with SessionLocal() as db:
        seed_report_data(db)

    response = client.get("/api/v1/reports/six-month?as_of_date=2026-04-17")

    assert response.status_code == 200
    payload = response.json()
    assert payload["range_start_date"] == "2025-11-01"
    assert payload["range_end_date"] == "2026-04-30"
    assert payload["month_count"] == 6
    assert len(payload["monthly_summaries"]) == 6
    march = next(
        month
        for month in payload["monthly_summaries"]
        if month["month_start_date"] == "2026-03-01"
    )
    april = next(
        month
        for month in payload["monthly_summaries"]
        if month["month_start_date"] == "2026-04-01"
    )
    assert march["workout_count"] == 2
    assert march["cardio_count"] == 2
    assert march["zone2_minutes"] == 35
    assert march["average_recovery_score"] == 80
    assert april["workout_count"] == 1
    assert april["average_daily_strain"] == 10
    assert payload["consistency_summary"]["weeks_with_workouts"] == 6
    assert "sparse" in payload["consistency_summary"]["summary_text"].lower()


def test_six_month_report_export_csv_has_stable_headers_and_order(client):
    with SessionLocal() as db:
        seed_report_data(db)

    response = client.get("/api/v1/reports/six-month/export.csv?as_of_date=2026-04-17")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in response.headers["content-disposition"]
    lines = response.text.strip().splitlines()
    header = lines[0].split(",")
    assert header == [
        "range_start_date",
        "range_end_date",
        "month_start_date",
        "month_end_date",
        "month_label",
        "workout_count",
        "sleep_count",
        "recovery_count",
        "training_seconds",
        "zone1_minutes",
        "zone2_minutes",
        "zone3_minutes",
        "zone4_minutes",
        "zone5_minutes",
        "cardio_count",
        "strength_count",
        "other_count",
        "unknown_count",
        "average_recovery_score",
        "average_daily_strain",
        "weeks_in_range",
        "active_weeks",
        "weeks_with_workouts",
        "weeks_with_sleeps",
        "weeks_with_recoveries",
        "training_week_coverage_percent",
        "sleep_week_coverage_percent",
        "recovery_week_coverage_percent",
        "summary_text",
    ]
    assert len(lines) == 7
