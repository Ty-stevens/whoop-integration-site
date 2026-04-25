from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from app.api.deps import require_api_auth
from app.api.routes import (
    ai,
    athlete_profile,
    dashboard,
    goals,
    health,
    recovery_strain,
    reports,
    sync,
    whoop,
    workouts,
)
from app.api.routes import settings as settings_routes
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import initialize_database


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    initialize_database(settings.database_url)

    docs_enabled = settings.api_docs_enabled and settings.app_env != "production"
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    app.include_router(health.router)
    app.include_router(health.api_router, prefix="/api/v1")
    app.include_router(whoop.router, prefix="/api/v1/integrations/whoop", tags=["whoop"])
    app.include_router(
        settings_routes.router,
        prefix="/api/v1/settings",
        tags=["settings"],
        dependencies=[Depends(require_api_auth)],
    )
    app.include_router(
        athlete_profile.router,
        prefix="/api/v1/athlete-profile",
        tags=["athlete-profile"],
        dependencies=[Depends(require_api_auth)],
    )
    app.include_router(
        dashboard.router,
        prefix="/api/v1/dashboard",
        tags=["dashboard"],
        dependencies=[Depends(require_api_auth)],
    )
    app.include_router(
        goals.router,
        prefix="/api/v1/goals",
        tags=["goals"],
        dependencies=[Depends(require_api_auth)],
    )
    app.include_router(
        sync.router,
        prefix="/api/v1/sync",
        tags=["sync"],
        dependencies=[Depends(require_api_auth)],
    )
    app.include_router(
        workouts.router,
        prefix="/api/v1/workouts",
        tags=["workouts"],
        dependencies=[Depends(require_api_auth)],
    )
    app.include_router(
        recovery_strain.router,
        prefix="/api/v1/recovery-strain",
        tags=["recovery-strain"],
        dependencies=[Depends(require_api_auth)],
    )
    app.include_router(
        reports.router,
        prefix="/api/v1/reports",
        tags=["reports"],
        dependencies=[Depends(require_api_auth)],
    )
    app.include_router(
        ai.router,
        prefix="/api/v1/ai",
        tags=["ai"],
        dependencies=[Depends(require_api_auth)],
    )

    return app


app = create_app()
