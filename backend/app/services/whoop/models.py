from datetime import datetime

from pydantic import BaseModel, Field


class WhoopTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = Field(gt=0)
    scope: str | None = None
    token_type: str | None = None
    whoop_user_id: str | None = None


class StoredWhoopTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_at_utc: datetime
    granted_scopes: str | None

