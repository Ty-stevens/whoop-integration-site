from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(health.api_router, prefix="/api/v1")
    app.include_router(whoop.router, prefix="/api/v1/integrations/whoop", tags=["whoop"])
    app.include_router(settings_routes.router, prefix="/api/v1/settings", tags=["settings"])
    app.include_router(
        athlete_profile.router,
        prefix="/api/v1/athlete-profile",
        tags=["athlete-profile"],
    )
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
    app.include_router(goals.router, prefix="/api/v1/goals", tags=["goals"])
    app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
    app.include_router(workouts.router, prefix="/api/v1/workouts", tags=["workouts"])
    app.include_router(
        recovery_strain.router,
        prefix="/api/v1/recovery-strain",
        tags=["recovery-strain"],
    )
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])

    return app


app = create_app()
