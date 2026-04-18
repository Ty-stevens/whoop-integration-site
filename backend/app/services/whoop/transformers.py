import hashlib
import json
from datetime import datetime
from typing import Any

from app.core.time import date_buckets_from_utc, ensure_utc, utc_now
from app.services.whoop.provider_models import WhoopRecovery, WhoopSleep, WhoopWorkout
from app.services.workouts.classification import classify_workout_sport


class TransformerError(ValueError):
    """Raised when a validated provider record cannot become a canonical fact."""


def stable_payload_hash(raw_payload: dict[str, Any]) -> str:
    payload_text = json.dumps(
        raw_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()


def milliseconds_to_seconds(value: int | None) -> int | None:
    if value is None:
        return None
    return value // 1000


def duration_seconds_between(start: datetime, end: datetime) -> int:
    start_utc = ensure_utc(start)
    end_utc = ensure_utc(end)
    if end_utc < start_utc:
        raise TransformerError("Provider end timestamp is before start timestamp")
    return int((end_utc - start_utc).total_seconds())


def _string_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _zone_seconds(value: int | None) -> int:
    return milliseconds_to_seconds(value) or 0


def _base_import_fields(raw_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_payload_json": raw_payload,
        "payload_hash": stable_payload_hash(raw_payload),
        "source_revision": 1,
        "imported_at_utc": utc_now(),
    }


def transform_workout(provider: WhoopWorkout, raw_payload: dict[str, Any]) -> dict[str, Any]:
    buckets = date_buckets_from_utc(provider.start, provider.timezone_offset)
    score = provider.score
    zones = score.zone_durations if score is not None else None

    values = {
        "external_id": provider.id,
        "external_v1_id": _string_or_none(provider.v1_id),
        "whoop_user_id": _string_or_none(provider.user_id),
        "external_created_at_utc": ensure_utc(provider.created_at)
        if provider.created_at is not None
        else None,
        "external_updated_at_utc": ensure_utc(provider.updated_at)
        if provider.updated_at is not None
        else None,
        "start_time_utc": ensure_utc(provider.start),
        "end_time_utc": ensure_utc(provider.end),
        "timezone_offset_text": provider.timezone_offset,
        "local_start_date": buckets.local_date,
        "iso_week_start_date": buckets.iso_week_start_date,
        "local_month_start_date": buckets.local_month_start_date,
        "sport_name": provider.sport_name,
        "score_state": provider.score_state,
        "classification": classify_workout_sport(provider.sport_name),
        "duration_seconds": duration_seconds_between(provider.start, provider.end),
        "strain": score.strain if score is not None else None,
        "average_hr": score.average_heart_rate if score is not None else None,
        "max_hr": score.max_heart_rate if score is not None else None,
        "percent_recorded": score.percent_recorded if score is not None else None,
        "zone0_seconds": _zone_seconds(zones.zone_zero_milli if zones is not None else None),
        "zone1_seconds": _zone_seconds(zones.zone_one_milli if zones is not None else None),
        "zone2_seconds": _zone_seconds(zones.zone_two_milli if zones is not None else None),
        "zone3_seconds": _zone_seconds(zones.zone_three_milli if zones is not None else None),
        "zone4_seconds": _zone_seconds(zones.zone_four_milli if zones is not None else None),
        "zone5_seconds": _zone_seconds(zones.zone_five_milli if zones is not None else None),
    }
    values.update(_base_import_fields(raw_payload))
    return values


def transform_sleep(provider: WhoopSleep, raw_payload: dict[str, Any]) -> dict[str, Any]:
    buckets = date_buckets_from_utc(provider.start, provider.timezone_offset)
    duration_seconds = duration_seconds_between(provider.start, provider.end)
    score = provider.score
    stage_summary = score.stage_summary if score is not None else None

    if stage_summary is None:
        sleep_duration_seconds = duration_seconds
    else:
        sleep_milliseconds = sum(
            value or 0
            for value in (
                stage_summary.total_light_sleep_time_milli,
                stage_summary.total_slow_wave_sleep_time_milli,
                stage_summary.total_rem_sleep_time_milli,
            )
        )
        sleep_duration_seconds = milliseconds_to_seconds(sleep_milliseconds) or 0

    values = {
        "external_id": provider.id,
        "external_v1_id": _string_or_none(provider.v1_id),
        "cycle_id": _string_or_none(provider.cycle_id),
        "whoop_user_id": _string_or_none(provider.user_id),
        "external_created_at_utc": ensure_utc(provider.created_at)
        if provider.created_at is not None
        else None,
        "external_updated_at_utc": ensure_utc(provider.updated_at)
        if provider.updated_at is not None
        else None,
        "start_time_utc": ensure_utc(provider.start),
        "end_time_utc": ensure_utc(provider.end),
        "timezone_offset_text": provider.timezone_offset,
        "local_start_date": buckets.local_date,
        "iso_week_start_date": buckets.iso_week_start_date,
        "local_month_start_date": buckets.local_month_start_date,
        "nap": bool(provider.nap),
        "score_state": provider.score_state,
        "sleep_duration_seconds": sleep_duration_seconds,
        "sleep_performance": score.sleep_performance_percentage if score is not None else None,
        "sleep_efficiency": score.sleep_efficiency_percentage if score is not None else None,
    }
    values.update(_base_import_fields(raw_payload))
    return values


def transform_recovery(provider: WhoopRecovery, raw_payload: dict[str, Any]) -> dict[str, Any]:
    bucket_timestamp = provider.updated_at or provider.created_at
    if bucket_timestamp is None:
        raise TransformerError("Recovery record is missing both updated_at and created_at")

    buckets = date_buckets_from_utc(bucket_timestamp)
    score = provider.score

    values = {
        "cycle_id": str(provider.cycle_id),
        "sleep_external_id": provider.sleep_id,
        "whoop_user_id": _string_or_none(provider.user_id),
        "external_created_at_utc": ensure_utc(provider.created_at)
        if provider.created_at is not None
        else None,
        "external_updated_at_utc": ensure_utc(provider.updated_at)
        if provider.updated_at is not None
        else None,
        "local_date": buckets.local_date,
        "iso_week_start_date": buckets.iso_week_start_date,
        "local_month_start_date": buckets.local_month_start_date,
        "score_state": provider.score_state,
        "recovery_score": score.recovery_score if score is not None else None,
        "hrv_ms": score.hrv_rmssd_milli if score is not None else None,
        "resting_hr": score.resting_heart_rate if score is not None else None,
        "respiratory_rate": None,
        "skin_temp_celsius": score.skin_temp_celsius if score is not None else None,
        "spo2_percent": score.spo2_percentage if score is not None else None,
    }
    values.update(_base_import_fields(raw_payload))
    return values
