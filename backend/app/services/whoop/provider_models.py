from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class WhoopProviderModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class WhoopCollectionResponse(WhoopProviderModel):
    next_token: str | None = None

    @field_validator("next_token", mode="before")
    @classmethod
    def empty_next_token_as_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


class WhoopWorkoutZoneDurations(WhoopProviderModel):
    zone_zero_milli: int | None = None
    zone_one_milli: int | None = None
    zone_two_milli: int | None = None
    zone_three_milli: int | None = None
    zone_four_milli: int | None = None
    zone_five_milli: int | None = None


class WhoopWorkoutScore(WhoopProviderModel):
    strain: float | None = None
    average_heart_rate: int | None = None
    max_heart_rate: int | None = None
    kilojoule: float | None = None
    percent_recorded: float | None = None
    distance_meter: float | None = None
    altitude_gain_meter: float | None = None
    altitude_change_meter: float | None = None
    zone_durations: WhoopWorkoutZoneDurations | None = None


class WhoopWorkout(WhoopProviderModel):
    id: str
    v1_id: int | None = None
    user_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    start: datetime
    end: datetime
    timezone_offset: str | None = None
    sport_name: str | None = None
    sport_id: int | None = None
    score_state: str
    score: WhoopWorkoutScore | None = None


class WhoopWorkoutCollectionResponse(WhoopCollectionResponse):
    records: list[WhoopWorkout]


class WhoopSleepStageSummary(WhoopProviderModel):
    total_in_bed_time_milli: int | None = None
    total_awake_time_milli: int | None = None
    total_no_data_time_milli: int | None = None
    total_light_sleep_time_milli: int | None = None
    total_slow_wave_sleep_time_milli: int | None = None
    total_rem_sleep_time_milli: int | None = None
    sleep_cycle_count: int | None = None
    disturbance_count: int | None = None


class WhoopSleepNeeded(WhoopProviderModel):
    baseline_milli: int | None = None
    need_from_sleep_debt_milli: int | None = None
    need_from_recent_strain_milli: int | None = None
    need_from_recent_nap_milli: int | None = None


class WhoopSleepScore(WhoopProviderModel):
    stage_summary: WhoopSleepStageSummary | None = None
    sleep_needed: WhoopSleepNeeded | None = None
    respiratory_rate: float | None = None
    sleep_performance_percentage: float | None = None
    sleep_consistency_percentage: float | None = None
    sleep_efficiency_percentage: float | None = None


class WhoopSleep(WhoopProviderModel):
    id: str
    cycle_id: int | None = None
    v1_id: int | None = None
    user_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    start: datetime
    end: datetime
    timezone_offset: str | None = None
    nap: bool | None = None
    score_state: str
    score: WhoopSleepScore | None = None


class WhoopSleepCollectionResponse(WhoopCollectionResponse):
    records: list[WhoopSleep]


class WhoopRecoveryScore(WhoopProviderModel):
    user_calibrating: bool | None = None
    recovery_score: float | None = None
    resting_heart_rate: int | None = None
    hrv_rmssd_milli: float | None = None
    spo2_percentage: float | None = None
    skin_temp_celsius: float | None = None


class WhoopRecovery(WhoopProviderModel):
    cycle_id: int
    sleep_id: str | None = None
    user_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    score_state: str
    score: WhoopRecoveryScore | None = None


class WhoopRecoveryCollectionResponse(WhoopCollectionResponse):
    records: list[WhoopRecovery]

