from datetime import UTC, date, datetime, timedelta

from app.db.session import SessionLocal
from app.models.facts import RecoveryModel, SleepModel, WorkoutModel
from app.services.metrics.six_month_report import SixMonthReportMetricsService
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
    zone1_seconds: int = 0,
    zone3_seconds: int = 0,
    zone4_seconds: int = 0,
    zone5_seconds: int = 0,
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
            "zone1_seconds": zone1_seconds,
            "zone2_seconds": zone2_seconds,
            "zone3_seconds": zone3_seconds,
            "zone4_seconds": zone4_seconds,
            "zone5_seconds": zone5_seconds,
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


def test_empty_six_month_report_returns_stable_months_and_null_averages():
    with SessionLocal() as db:
        summary = SixMonthReportMetricsService(db).build(date(2026, 4, 17))

    assert summary.range_start_date == date(2025, 11, 1)
    assert summary.range_end_date == date(2026, 4, 30)
    assert summary.month_count == 6
    assert len(summary.monthly_summaries) == 6
    assert all(month.workout_count == 0 for month in summary.monthly_summaries)
    assert all(month.average_recovery_score is None for month in summary.monthly_summaries)
    assert summary.consistency_summary.weeks_in_range > 0
    assert summary.consistency_summary.active_weeks == 0
    assert summary.consistency_summary.summary_text.startswith("No training")


def test_populated_six_month_report_aggregates_months_and_consistency():
    with SessionLocal() as db:
        # November 2025
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
            zone1_seconds=600,
            zone2_seconds=1200,
            zone3_seconds=300,
            zone4_seconds=0,
            zone5_seconds=0,
        )

        # December 2025
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
            zone1_seconds=300,
            zone2_seconds=1800,
            zone3_seconds=600,
        )

        # January 2026
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
            zone1_seconds=0,
            zone2_seconds=900,
            zone3_seconds=900,
            zone4_seconds=300,
        )

        # February 2026
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
            zone1_seconds=0,
            zone2_seconds=600,
            zone3_seconds=600,
            zone4_seconds=0,
            zone5_seconds=300,
        )

        # March 2026
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
            zone1_seconds=300,
            zone2_seconds=1500,
            zone3_seconds=300,
        )
        create_workout(
            db,
            external_id="workout-6",
            start_date=date(2026, 3, 19),
            week_start=date(2026, 3, 16),
            month_start=date(2026, 3, 1),
            classification="cardio",
            strain=9.5,
            zone1_seconds=0,
            zone2_seconds=600,
            zone3_seconds=600,
            zone4_seconds=600,
        )

        # April 2026
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
            zone1_seconds=0,
            zone2_seconds=1800,
            zone3_seconds=600,
            zone4_seconds=300,
            zone5_seconds=0,
        )

        summary = SixMonthReportMetricsService(db).build(date(2026, 4, 17))

    march = next(
        month
        for month in summary.monthly_summaries
        if month.month_start_date == date(2026, 3, 1)
    )
    april = next(
        month
        for month in summary.monthly_summaries
        if month.month_start_date == date(2026, 4, 1)
    )

    assert march.workout_count == 2
    assert march.cardio_count == 2
    assert march.zone2_minutes == 35
    assert march.average_recovery_score == 80
    assert march.average_daily_strain == 9.25
    assert april.workout_count == 1
    assert april.cardio_count == 1
    assert april.zone2_minutes == 30
    assert april.average_recovery_score == 82
    assert april.average_daily_strain == 10
    assert summary.consistency_summary.active_weeks == 6
    assert summary.consistency_summary.weeks_with_workouts == 6
    assert summary.consistency_summary.training_week_coverage_percent is not None
    assert "sparse" in summary.consistency_summary.summary_text.lower()
