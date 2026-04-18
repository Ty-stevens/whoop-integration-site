import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from app.db.session import SessionLocal
from app.repositories.recoveries import RecoveryRepository
from app.repositories.sleeps import SleepRepository
from app.repositories.workouts import WorkoutRepository
from app.services.whoop.provider_models import (
    WhoopRecoveryCollectionResponse,
    WhoopSleepCollectionResponse,
    WhoopWorkoutCollectionResponse,
)
from app.services.whoop.transformers import (
    TransformerError,
    duration_seconds_between,
    stable_payload_hash,
    transform_recovery,
    transform_sleep,
    transform_workout,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "whoop"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_payload_hash_ignores_key_order_but_preserves_value_changes():
    payload_a = {"id": "record-1", "score": {"strain": 8.2, "zones": [1, 2, 3]}}
    payload_b = {"score": {"zones": [1, 2, 3], "strain": 8.2}, "id": "record-1"}
    payload_c = {"id": "record-1", "score": {"strain": 8.3, "zones": [1, 2, 3]}}

    assert stable_payload_hash(payload_a) == stable_payload_hash(payload_b)
    assert stable_payload_hash(payload_a) != stable_payload_hash(payload_c)


def test_workout_transform_maps_scored_metrics_zones_and_buckets():
    payload = load_fixture("workout_collection_scored.json")
    provider = WhoopWorkoutCollectionResponse.model_validate(payload).records[0]
    values = transform_workout(provider, payload["records"][0])

    assert values["external_id"] == "11111111-1111-4111-8111-111111111111"
    assert values["external_v1_id"] == "1043"
    assert values["whoop_user_id"] == "9012"
    assert values["local_start_date"] == date(2022, 4, 23)
    assert values["iso_week_start_date"] == date(2022, 4, 18)
    assert values["local_month_start_date"] == date(2022, 4, 1)
    assert values["classification"] == "cardio"
    assert values["duration_seconds"] == 28800
    assert values["strain"] == 8.2463
    assert values["average_hr"] == 123
    assert values["max_hr"] == 146
    assert values["percent_recorded"] == 100
    assert values["zone0_seconds"] == 300
    assert values["zone1_seconds"] == 600
    assert values["zone2_seconds"] == 900
    assert values["zone3_seconds"] == 900
    assert values["zone4_seconds"] == 600
    assert values["zone5_seconds"] == 300
    assert values["raw_payload_json"]["synthetic_future_field"] == "kept"
    assert len(values["payload_hash"]) == 64
    assert values["source_revision"] == 1
    assert values["imported_at_utc"].tzinfo is not None


def test_workout_transform_maps_pending_score_to_null_metrics_and_zero_zones():
    payload = load_fixture("workout_collection_pending.json")
    provider = WhoopWorkoutCollectionResponse.model_validate(payload).records[0]
    values = transform_workout(provider, payload["records"][0])

    assert values["score_state"] == "PENDING_SCORE"
    assert values["strain"] is None
    assert values["average_hr"] is None
    assert values["max_hr"] is None
    assert values["percent_recorded"] is None
    assert values["zone0_seconds"] == 0
    assert values["zone1_seconds"] == 0
    assert values["zone2_seconds"] == 0
    assert values["zone3_seconds"] == 0
    assert values["zone4_seconds"] == 0
    assert values["zone5_seconds"] == 0


def test_negative_duration_raises_transformer_error():
    with pytest.raises(TransformerError, match="end timestamp is before start"):
        duration_seconds_between(
            datetime(2026, 4, 14, 12, tzinfo=UTC),
            datetime(2026, 4, 14, 11, tzinfo=UTC),
        )


def test_sleep_transform_uses_actual_sleep_stage_duration_for_scored_sleep():
    payload = load_fixture("sleep_collection_scored.json")
    provider = WhoopSleepCollectionResponse.model_validate(payload).records[0]
    values = transform_sleep(provider, payload["records"][0])

    assert values["external_id"] == "33333333-3333-4333-8333-333333333333"
    assert values["cycle_id"] == "93845"
    assert values["local_start_date"] == date(2022, 4, 23)
    assert values["sleep_duration_seconds"] == 27415
    assert values["sleep_performance"] == 98
    assert values["sleep_efficiency"] == 91.69533848
    assert values["nap"] is False
    assert len(values["payload_hash"]) == 64


def test_sleep_transform_rejects_negative_duration_even_with_stage_summary():
    payload = load_fixture("sleep_collection_scored.json")
    provider = WhoopSleepCollectionResponse.model_validate(payload).records[0]
    provider = provider.model_copy(
        update={"end": datetime(2022, 4, 24, 1, 25, 44, 774000, tzinfo=UTC)}
    )

    with pytest.raises(TransformerError, match="end timestamp is before start"):
        transform_sleep(provider, payload["records"][0])


def test_sleep_transform_falls_back_to_start_end_duration_for_pending_sleep():
    payload = load_fixture("sleep_collection_pending.json")
    provider = WhoopSleepCollectionResponse.model_validate(payload).records[0]
    values = transform_sleep(provider, payload["records"][0])

    assert values["score_state"] == "PENDING_SCORE"
    assert values["sleep_duration_seconds"] == 28800
    assert values["sleep_performance"] is None
    assert values["sleep_efficiency"] is None


def test_recovery_transform_maps_scored_metrics_and_date_buckets():
    payload = load_fixture("recovery_collection_scored.json")
    provider = WhoopRecoveryCollectionResponse.model_validate(payload).records[0]
    values = transform_recovery(provider, payload["records"][0])

    assert values["cycle_id"] == "93845"
    assert values["sleep_external_id"] == "33333333-3333-4333-8333-333333333333"
    assert values["whoop_user_id"] == "10129"
    assert values["local_date"] == date(2022, 4, 24)
    assert values["iso_week_start_date"] == date(2022, 4, 18)
    assert values["local_month_start_date"] == date(2022, 4, 1)
    assert values["recovery_score"] == 44
    assert values["hrv_ms"] == 31.813562
    assert values["resting_hr"] == 64
    assert values["spo2_percent"] == 95.6875
    assert values["skin_temp_celsius"] == 33.7
    assert values["respiratory_rate"] is None


def test_recovery_transform_maps_partial_pending_score_to_null_metrics():
    payload = load_fixture("recovery_collection_pending.json")
    provider = WhoopRecoveryCollectionResponse.model_validate(payload).records[0]
    values = transform_recovery(provider, payload["records"][0])

    assert values["score_state"] == "PENDING_SCORE"
    assert values["recovery_score"] is None
    assert values["hrv_ms"] is None
    assert values["resting_hr"] is None
    assert values["spo2_percent"] is None
    assert values["skin_temp_celsius"] is None


def test_recovery_transform_requires_bucket_timestamp():
    payload = load_fixture("recovery_collection_pending.json")
    provider = WhoopRecoveryCollectionResponse.model_validate(payload).records[0]
    provider = provider.model_copy(update={"created_at": None, "updated_at": None})

    with pytest.raises(TransformerError, match="missing both updated_at and created_at"):
        transform_recovery(provider, payload["records"][0])


def test_transformed_records_upsert_through_fact_repositories():
    workout_payload = load_fixture("workout_collection_scored.json")
    sleep_payload = load_fixture("sleep_collection_scored.json")
    recovery_payload = load_fixture("recovery_collection_scored.json")

    workout_provider = WhoopWorkoutCollectionResponse.model_validate(workout_payload).records[0]
    sleep_provider = WhoopSleepCollectionResponse.model_validate(sleep_payload).records[0]
    recovery_provider = WhoopRecoveryCollectionResponse.model_validate(recovery_payload).records[0]

    workout_values = transform_workout(workout_provider, workout_payload["records"][0])
    sleep_values = transform_sleep(sleep_provider, sleep_payload["records"][0])
    recovery_values = transform_recovery(recovery_provider, recovery_payload["records"][0])

    with SessionLocal() as db:
        workout_result = WorkoutRepository(db).upsert(workout_values)
        sleep_result = SleepRepository(db).upsert(sleep_values)
        recovery_result = RecoveryRepository(db).upsert(recovery_values)

    assert workout_result.inserted is True
    assert workout_result.row.source_revision == 1
    assert sleep_result.inserted is True
    assert sleep_result.row.source_revision == 1
    assert recovery_result.inserted is True
    assert recovery_result.row.source_revision == 1
