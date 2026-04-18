from datetime import UTC, date, datetime

import pytest

from app.core.time import (
    date_buckets_from_utc,
    local_date_from_utc,
    parse_timezone_offset,
)


def test_monday_utc_timestamp_resolves_to_same_iso_week_monday():
    buckets = date_buckets_from_utc(datetime(2026, 4, 6, 12, tzinfo=UTC), "+00:00")

    assert buckets.local_date == date(2026, 4, 6)
    assert buckets.iso_week_start_date == date(2026, 4, 6)
    assert buckets.local_month_start_date == date(2026, 4, 1)


def test_sunday_local_date_resolves_to_previous_monday():
    buckets = date_buckets_from_utc(datetime(2026, 4, 12, 12, tzinfo=UTC), "+00:00")

    assert buckets.local_date == date(2026, 4, 12)
    assert buckets.iso_week_start_date == date(2026, 4, 6)


def test_negative_offset_can_shift_near_midnight_to_previous_local_day():
    local_date = local_date_from_utc(datetime(2026, 4, 6, 2, 30, tzinfo=UTC), "-05:00")

    assert local_date == date(2026, 4, 5)


def test_positive_offset_can_shift_near_midnight_to_next_local_day():
    buckets = date_buckets_from_utc(datetime(2026, 4, 30, 23, 30, tzinfo=UTC), "+02:00")

    assert buckets.local_date == date(2026, 5, 1)
    assert buckets.local_month_start_date == date(2026, 5, 1)


def test_missing_offset_defaults_to_utc():
    buckets = date_buckets_from_utc(datetime(2026, 4, 6, 0, 30, tzinfo=UTC))

    assert buckets.local_date == date(2026, 4, 6)


def test_naive_datetime_is_treated_as_utc():
    buckets = date_buckets_from_utc(datetime(2026, 4, 6, 0, 30), "+00:00")

    assert buckets.local_date == date(2026, 4, 6)


@pytest.mark.parametrize("bad_offset", ["UTC", "+24:00", "+02:60", "2:00", "+0200"])
def test_invalid_offset_text_raises_clear_error(bad_offset):
    with pytest.raises(ValueError, match="Timezone offset"):
        parse_timezone_offset(bad_offset)

