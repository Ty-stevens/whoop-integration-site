from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.api.deps import DbSession, require_api_auth
from app.core.config import Settings, get_settings
from app.schemas.whoop import WhoopConnectStart, WhoopConnectUnavailable, WhoopStatus
from app.services.whoop.auth_service import WhoopAuthService
from app.services.whoop.oauth import OAuthStateError

router = APIRouter()


def _frontend_redirect_base(request: Request, settings: Settings) -> str:
    if settings.app_env == "development":
        return settings.frontend_dev_url.rstrip("/")

    app_base = settings.app_base_url.strip() if settings.app_base_url else ""
    if app_base:
        return app_base.rstrip("/")

    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_host:
        host = forwarded_host.split(",", 1)[0].strip()
    else:
        host = request.headers.get("host") or request.url.hostname or ""

    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    return f"{scheme}://{host}".rstrip("/")


def _trim_backend_prefix(frontend_base_url: str) -> str:
    """Remove service prefixes so we always redirect to the Vite app root."""
    for suffix in ("/backend", "/backend/"):
        if frontend_base_url.endswith(suffix):
            return frontend_base_url[: -len(suffix)].rstrip("/")
    return frontend_base_url


@router.get("/status", response_model=WhoopStatus)
def whoop_status(
    db: DbSession,
    _: None = Depends(require_api_auth),
) -> WhoopStatus:
    return WhoopAuthService(db).status()


@router.get("/connect", response_model=None)
def whoop_connect(
    db: DbSession,
    _: None = Depends(require_api_auth),
):
    settings = get_settings()
    if settings.database_is_ephemeral:
        raise HTTPException(status_code=503, detail=settings.database_storage_message)
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


@router.get("/connect/start", response_model=WhoopConnectStart)
def whoop_connect_start(
    db: DbSession,
    _: None = Depends(require_api_auth),
) -> WhoopConnectStart:
    settings = get_settings()
    if settings.database_is_ephemeral:
        raise HTTPException(status_code=503, detail=settings.database_storage_message)
    if not settings.whoop_credentials_configured:
        raise HTTPException(
            status_code=503,
            detail="WHOOP credentials are not configured. Local boot does not require them.",
        )
    authorization_url = WhoopAuthService(db).authorization_url()
    if authorization_url is None:
        raise HTTPException(
            status_code=503,
            detail="WHOOP credentials are not configured. Local boot does not require them.",
        )
    return WhoopConnectStart(authorization_url=authorization_url)


@router.get("/callback")
def whoop_callback(
    request: Request,
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
) -> RedirectResponse:
    settings = get_settings()
    if settings.database_is_ephemeral:
        raise HTTPException(status_code=503, detail=settings.database_storage_message)
    if not code or not state:
        raise HTTPException(status_code=400, detail="WHOOP callback requires code and state")
    try:
        WhoopAuthService(db).handle_callback(code=code, state=state)
    except OAuthStateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    frontend_base_url = _trim_backend_prefix(
        _frontend_redirect_base(request, settings=settings)
    )
    return RedirectResponse(f"{frontend_base_url}/settings?whoop=connected")


@router.post("/disconnect")
def whoop_disconnect(
    db: DbSession,
    _: None = Depends(require_api_auth),
) -> dict[str, str]:
    WhoopAuthService(db).disconnect()
    return {
        "status": "disconnected",
        "message": "WHOOP connection removed from local storage.",
    }
