from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class WhoopStatus(BaseModel):
    status: Literal[
        "disconnected",
        "connected",
        "expired",
        "error",
        "config_missing",
    ] = "disconnected"
    credentials_configured: bool
    connected_at_utc: datetime | None = None
    last_token_refresh_at_utc: datetime | None = None
    token_expires_at_utc: datetime | None = None
    granted_scopes: str | None = None
    message: str


class WhoopConnectUnavailable(BaseModel):
    status: Literal["config_missing"] = "config_missing"
    message: str


class WhoopConnectStart(BaseModel):
    authorization_url: str
