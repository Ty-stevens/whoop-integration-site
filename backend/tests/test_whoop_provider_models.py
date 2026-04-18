import json
from datetime import datetime
from pathlib import Path

from app.services.whoop.provider_models import (
    WhoopRecoveryCollectionResponse,
    WhoopSleepCollectionResponse,
    WhoopWorkoutCollectionResponse,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "whoop"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_workout_collection_parses_scored_record_and_pagination():
    payload = load_fixture("workout_collection_scored.json")
    response = WhoopWorkoutCollectionResponse.model_validate(payload)

    workout = response.records[0]
    assert response.next_token == "next-workout-page"
    assert isinstance(workout.start, datetime)
    assert workout.score is not None
    assert workout.score.strain == 8.2463
    assert workout.score.zone_durations is not None
    assert workout.score.zone_durations.zone_two_milli == 900000
    assert workout.model_dump()["synthetic_future_field"] == "kept"


def test_workout_collection_parses_pending_record_without_score():
    payload = load_fixture("workout_collection_pending.json")
    response = WhoopWorkoutCollectionResponse.model_validate(payload)

    workout = response.records[0]
    assert response.next_token is None
    assert workout.score_state == "PENDING_SCORE"
    assert workout.score is None


def test_sleep_collection_parses_scored_record_and_pagination():
    payload = load_fixture("sleep_collection_scored.json")
    response = WhoopSleepCollectionResponse.model_validate(payload)

    sleep = response.records[0]
    assert response.next_token == "next-sleep-page"
    assert isinstance(sleep.updated_at, datetime)
    assert sleep.score is not None
    assert sleep.score.stage_summary is not None
    assert sleep.score.stage_summary.total_in_bed_time_milli == 30272735
    assert sleep.score.sleep_needed is not None
    assert sleep.score.sleep_needed.need_from_recent_nap_milli == -12312
    assert sleep.score.sleep_efficiency_percentage == 91.69533848


def test_sleep_collection_parses_pending_record_with_empty_next_token():
    payload = load_fixture("sleep_collection_pending.json")
    response = WhoopSleepCollectionResponse.model_validate(payload)

    sleep = response.records[0]
    assert response.next_token is None
    assert sleep.score_state == "PENDING_SCORE"
    assert sleep.score is None


def test_recovery_collection_parses_scored_record_and_pagination():
    payload = load_fixture("recovery_collection_scored.json")
    response = WhoopRecoveryCollectionResponse.model_validate(payload)

    recovery = response.records[0]
    assert response.next_token == "next-recovery-page"
    assert isinstance(recovery.created_at, datetime)
    assert recovery.score is not None
    assert recovery.score.recovery_score == 44
    assert recovery.score.hrv_rmssd_milli == 31.813562
    assert recovery.score.resting_heart_rate == 64
    assert recovery.score.spo2_percentage == 95.6875
    assert recovery.score.skin_temp_celsius == 33.7


def test_recovery_collection_parses_pending_record_with_partial_score():
    payload = load_fixture("recovery_collection_pending.json")
    response = WhoopRecoveryCollectionResponse.model_validate(payload)

    recovery = response.records[0]
    assert response.next_token is None
    assert recovery.score_state == "PENDING_SCORE"
    assert recovery.score is not None
    assert recovery.score.user_calibrating is True
    assert recovery.score.recovery_score is None

