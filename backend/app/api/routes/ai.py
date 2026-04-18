from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.config import get_settings
from app.schemas.ai import AiGoalSuggestionsResponse, AiStatusResponse, AiWeeklySummaryResponse
from app.services.ai.summary_service import AiSummaryService

router = APIRouter()


@router.get("/status", response_model=AiStatusResponse)
def ai_status() -> AiStatusResponse:
    settings = get_settings()
    if not settings.ai_enabled:
        return AiStatusResponse(
            status="disabled",
            provider=settings.ai_provider,
            enabled=False,
            model=settings.ai_model or None,
            message="AI is disabled.",
        )
    configured = bool(settings.ai_base_url and settings.ai_model)
    message = "AI provider is configured." if configured else "AI provider settings are incomplete."
    return AiStatusResponse(
        status="configured" if configured else "failing",
        provider=settings.ai_provider,
        enabled=True,
        model=settings.ai_model or None,
        message=message,
    )


@router.post("/weekly-summary", response_model=AiWeeklySummaryResponse)
def weekly_summary(db: DbSession) -> AiWeeklySummaryResponse:
    return AiSummaryService(db).weekly_summary()


@router.post("/goal-suggestions", response_model=AiGoalSuggestionsResponse)
def goal_suggestions(db: DbSession) -> AiGoalSuggestionsResponse:
    return AiSummaryService(db).goal_suggestions()
