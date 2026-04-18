from datetime import UTC, date, datetime


def workout_values(
    *,
    external_id: str = "workout-1",
    external_updated_at_utc: datetime | None = None,
    payload_hash: str = "hash-1",
    raw_payload_json: dict | None = None,
) -> dict:
    return {
        "external_id": external_id,
        "external_v1_id": None,
        "whoop_user_id": "whoop-user-1",
        "external_created_at_utc": datetime(2026, 4, 1, 10, tzinfo=UTC),
        "external_updated_at_utc": external_updated_at_utc
        or datetime(2026, 4, 1, 11, tzinfo=UTC),
        "start_time_utc": datetime(2026, 4, 6, 7, tzinfo=UTC),
        "end_time_utc": datetime(2026, 4, 6, 8, tzinfo=UTC),
        "timezone_offset_text": "+00:00",
        "local_start_date": date(2026, 4, 6),
        "iso_week_start_date": date(2026, 4, 6),
        "local_month_start_date": date(2026, 4, 1),
        "sport_name": "Running",
        "score_state": "SCORED",
        "classification": "cardio",
        "duration_seconds": 3600,
        "strain": 10.5,
        "average_hr": 142,
        "max_hr": 171,
        "percent_recorded": 99.0,
        "zone0_seconds": 100,
        "zone1_seconds": 500,
        "zone2_seconds": 2000,
        "zone3_seconds": 700,
        "zone4_seconds": 250,
        "zone5_seconds": 50,
        "raw_payload_json": raw_payload_json or {"id": external_id},
        "payload_hash": payload_hash,
        "source_revision": 1,
        "imported_at_utc": datetime(2026, 4, 6, 9, tzinfo=UTC),
    }


def sleep_values(
    *,
    external_id: str = "sleep-1",
    payload_hash: str = "sleep-hash-1",
) -> dict:
    return {
        "external_id": external_id,
        "external_v1_id": None,
        "cycle_id": "cycle-1",
        "whoop_user_id": "whoop-user-1",
        "external_created_at_utc": datetime(2026, 4, 6, 6, tzinfo=UTC),
        "external_updated_at_utc": datetime(2026, 4, 6, 7, tzinfo=UTC),
        "start_time_utc": datetime(2026, 4, 5, 22, tzinfo=UTC),
        "end_time_utc": datetime(2026, 4, 6, 6, tzinfo=UTC),
        "timezone_offset_text": "+00:00",
        "local_start_date": date(2026, 4, 5),
        "iso_week_start_date": date(2026, 3, 30),
        "local_month_start_date": date(2026, 4, 1),
        "nap": False,
        "score_state": "SCORED",
        "sleep_duration_seconds": 28800,
        "sleep_performance": 91.0,
        "sleep_efficiency": 88.0,
        "raw_payload_json": {"id": external_id},
        "payload_hash": payload_hash,
        "source_revision": 1,
        "imported_at_utc": datetime(2026, 4, 6, 8, tzinfo=UTC),
    }


def recovery_values(
    *,
    cycle_id: str = "cycle-1",
    payload_hash: str = "recovery-hash-1",
) -> dict:
    return {
        "cycle_id": cycle_id,
        "sleep_external_id": "sleep-1",
        "whoop_user_id": "whoop-user-1",
        "external_created_at_utc": datetime(2026, 4, 6, 6, tzinfo=UTC),
        "external_updated_at_utc": datetime(2026, 4, 6, 7, tzinfo=UTC),
        "local_date": date(2026, 4, 6),
        "iso_week_start_date": date(2026, 4, 6),
        "local_month_start_date": date(2026, 4, 1),
        "score_state": "SCORED",
        "recovery_score": 72.0,
        "hrv_ms": 61.5,
        "resting_hr": 48,
        "respiratory_rate": 14.2,
        "skin_temp_celsius": 36.4,
        "spo2_percent": 98.0,
        "raw_payload_json": {"cycle_id": cycle_id},
        "payload_hash": payload_hash,
        "source_revision": 1,
        "imported_at_utc": datetime(2026, 4, 6, 8, tzinfo=UTC),
    }

