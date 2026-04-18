from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import generate_state_token
from app.core.time import ensure_utc
from app.models.oauth_state import OAuthStateModel

WHOOP_SCOPES = "read:profile read:cycles read:recovery read:sleep read:workout"


class OAuthStateError(ValueError):
    pass


def create_oauth_state(db: Session, provider: str = "whoop") -> str:
    state = generate_state_token()
    db.add(
        OAuthStateModel(
            provider=provider,
            state=state,
            expires_at_utc=datetime.now(UTC) + timedelta(minutes=10),
        )
    )
    db.commit()
    return state


def consume_oauth_state(db: Session, state: str, provider: str = "whoop") -> None:
    row = db.scalar(
        select(OAuthStateModel).where(
            OAuthStateModel.provider == provider,
            OAuthStateModel.state == state,
        )
    )
    if row is None:
        raise OAuthStateError("Unknown OAuth state")
    if row.consumed_at_utc is not None:
        raise OAuthStateError("OAuth state has already been used")
    if ensure_utc(row.expires_at_utc) < datetime.now(UTC):
        raise OAuthStateError("OAuth state has expired")
    row.consumed_at_utc = datetime.now(UTC)
    db.commit()


def build_authorization_url(settings: Settings, state: str) -> str:
    params = urlencode(
        {
            "client_id": settings.whoop_client_id,
            "redirect_uri": settings.whoop_redirect_uri,
            "response_type": "code",
            "scope": WHOOP_SCOPES,
            "state": state,
        }
    )
    return f"{settings.whoop_authorization_url}?{params}"

