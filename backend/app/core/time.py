import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def iso_week_start(value: date) -> date:
    return date.fromisocalendar(value.isocalendar().year, value.isocalendar().week, 1)


@dataclass(frozen=True)
class DateBuckets:
    local_date: date
    iso_week_start_date: date
    local_month_start_date: date


def parse_timezone_offset(offset_text: str | None) -> timezone:
    if offset_text is None or offset_text.strip() == "":
        return UTC

    match = re.fullmatch(r"([+-])(\d{2}):(\d{2})", offset_text.strip())
    if match is None:
        raise ValueError("Timezone offset must use +HH:MM or -HH:MM format")

    sign_text, hours_text, minutes_text = match.groups()
    hours = int(hours_text)
    minutes = int(minutes_text)
    if hours > 23 or minutes > 59:
        raise ValueError("Timezone offset is outside valid hour/minute bounds")

    delta = timedelta(hours=hours, minutes=minutes)
    if sign_text == "-":
        delta = -delta
    return timezone(delta)


def local_date_from_utc(timestamp_utc: datetime, offset_text: str | None = None) -> date:
    return ensure_utc(timestamp_utc).astimezone(parse_timezone_offset(offset_text)).date()


def month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def date_buckets_from_utc(timestamp_utc: datetime, offset_text: str | None = None) -> DateBuckets:
    local_date = local_date_from_utc(timestamp_utc, offset_text)
    return DateBuckets(
        local_date=local_date,
        iso_week_start_date=iso_week_start(local_date),
        local_month_start_date=month_start(local_date),
    )
