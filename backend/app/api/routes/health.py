from fastapi import APIRouter

from app.core.config import get_settings
from app.db.session import check_database

router = APIRouter(tags=["health"])
api_router = APIRouter(tags=["health"])


def health_payload() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "app": settings.app_name,
        "status": "ok",
        "environment": settings.app_env,
        "version": settings.app_version,
        "database": check_database(),
        "api_auth_required": settings.api_auth_enabled,
    }


@router.get("/health")
def root_health() -> dict[str, str | bool]:
    return health_payload()


@api_router.get("/health")
def api_health() -> dict[str, str | bool]:
    return health_payload()
