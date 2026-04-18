from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.api.deps import DbSession
from app.core.config import get_settings
from app.schemas.whoop import WhoopConnectUnavailable, WhoopStatus
from app.services.whoop.auth_service import WhoopAuthService
from app.services.whoop.oauth import OAuthStateError

router = APIRouter()


@router.get("/status", response_model=WhoopStatus)
def whoop_status(db: DbSession) -> WhoopStatus:
    return WhoopAuthService(db).status()


@router.get("/connect", response_model=None)
def whoop_connect(db: DbSession):
    settings = get_settings()
    if not settings.whoop_credentials_configured:
        return WhoopStatus(
            status="config_missing",
            credentials_configured=False,
            message="WHOOP credentials are not configured. Local boot does not require them.",
        )
    authorization_url = WhoopAuthService(db).authorization_url()
    if authorization_url is None:
        return WhoopConnectUnavailable(
            message="WHOOP credentials are not configured. Local boot does not require them."
        )
    return RedirectResponse(authorization_url)


@router.get("/callback")
def whoop_callback(
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
) -> RedirectResponse:
    if not code or not state:
        raise HTTPException(status_code=400, detail="WHOOP callback requires code and state")
    try:
        WhoopAuthService(db).handle_callback(code=code, state=state)
    except OAuthStateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return RedirectResponse(f"{get_settings().frontend_dev_url}/settings?whoop=connected")


@router.post("/disconnect")
def whoop_disconnect(db: DbSession) -> dict[str, str]:
    WhoopAuthService(db).disconnect()
    return {
        "status": "disconnected",
        "message": "WHOOP connection removed from local storage.",
    }
