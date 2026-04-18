from typing import Literal

from pydantic import BaseModel


class AppSettings(BaseModel):
    auto_sync_enabled: bool = False
    auto_sync_frequency: Literal["daily", "twice_daily"] = "daily"
    preferred_export_format: Literal["csv"] = "csv"
    preferred_units: Literal["metric", "imperial"] = "metric"

