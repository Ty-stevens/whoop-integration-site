from datetime import UTC, date, datetime, timedelta

from app.db.session import SessionLocal
from app.models.facts import RecoveryModel, SleepModel, WorkoutModel
from app.services.metrics.recovery_strain import RecoveryStrainMetricsService
from tests.fact_fixtures import recovery_values, sleep_values, workout_values


def create_workout(
    db,
    *,
    external_id: str,
    start_date: date,
    week_start: date,
    month_start: date,
    classification: str = "cardio",
    strain: float | None = 7.0,
    zone2_seconds: int = 1800,
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
    recovery_score: float | None = 70.0,
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


def test_empty_trends_return_calm_valid_payload():
    with SessionLocal() as db:
        summary = RecoveryStrainMetricsService(db).build(date(2026, 4, 17))

    assert summary.range_start_week == date(2026, 1, 26)
    assert summary.range_end_week == date(2026, 4, 13)
    assert len(summary.weekly_series) == 12
    assert all(point.workout_count == 0 for point in summary.weekly_series)
    assert all(point.average_recovery_score is None for point in summary.weekly_series)
    assert all(card.direction == "insufficient" for card in summary.comparison_cards)
    assert summary.data_state == "empty"
    assert "not enough" in summary.interpretation_text.lower()


def test_populated_trends_build_weekly_series_and_rolling_cards():
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
                zone2_seconds=1200 + offset * 60,
            )

        summary = RecoveryStrainMetricsService(db).build(date(2026, 4, 17))

    assert len(summary.weekly_series) == 12
    active_week = next(
        point for point in summary.weekly_series if point.week_start_date == date(2026, 4, 6)
    )
    assert active_week.workout_count == 1
    assert active_week.sleep_count == 1
    assert active_week.recovery_count == 1
    assert active_week.average_recovery_score == 81
    assert active_week.average_daily_strain == 6.25
    assert active_week.recovery_per_strain == 12.96

    recovery_card = next(card for card in summary.comparison_cards if card.metric == "recovery")
    strain_card = next(card for card in summary.comparison_cards if card.metric == "strain")
    assert recovery_card.current_average == 78.0
    assert recovery_card.previous_average == 67.5
    assert recovery_card.delta == 10.5
    assert recovery_card.direction == "up"
    assert strain_card.current_average == 6.5
    assert strain_card.previous_average == 7.38
    assert strain_card.delta == -0.88
    assert strain_card.direction == "down"
    assert summary.data_state == "ready"
    assert summary.interpretation_text == "Recovery is moving up while strain is steady or easing."


def test_partial_trends_with_single_window_of_data_stay_calm():
    with SessionLocal() as db:
        create_workout(
            db,
            external_id="workout-1",
            start_date=date(2026, 4, 8),
            week_start=date(2026, 4, 6),
            month_start=date(2026, 4, 1),
            strain=6.0,
        )
        create_recovery(
            db,
            cycle_id="cycle-1",
            local_date=date(2026, 4, 8),
            week_start=date(2026, 4, 6),
            month_start=date(2026, 4, 1),
            recovery_score=80,
        )

        summary = RecoveryStrainMetricsService(db).build(date(2026, 4, 17))

    recovery_card = next(card for card in summary.comparison_cards if card.metric == "recovery")
    assert recovery_card.has_enough_history is False
    assert summary.data_state == "partial"
    assert "sparse" in summary.interpretation_text.lower()
