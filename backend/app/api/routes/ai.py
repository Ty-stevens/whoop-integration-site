from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.config import get_settings
from app.schemas.ai import (
    AiBenchmarkUpdateRequest,
    AiBenchmarkUpdateResponse,
    AiGoalSuggestionsResponse,
    AiStatusResponse,
    AiWeeklySummaryResponse,
)
from app.services.ai.benchmark_service import AiBenchmarkService
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
    setup_error = settings.ai_setup_error
    configured = setup_error is None
    message = "AI provider is configured." if configured else setup_error
    return AiStatusResponse(
        status="configured" if configured else "failing",
        provider=settings.ai_provider,
        enabled=True,
        model=settings.effective_ai_model or None,
        message=message,
    )


@router.post("/weekly-summary", response_model=AiWeeklySummaryResponse)
def weekly_summary(db: DbSession) -> AiWeeklySummaryResponse:
    return AiSummaryService(db).weekly_summary()


@router.post("/goal-suggestions", response_model=AiGoalSuggestionsResponse)
def goal_suggestions(db: DbSession) -> AiGoalSuggestionsResponse:
    return AiSummaryService(db).goal_suggestions()


@router.post("/benchmark-update", response_model=AiBenchmarkUpdateResponse)
def benchmark_update(
    payload: AiBenchmarkUpdateRequest,
    db: DbSession,
) -> AiBenchmarkUpdateResponse:
    return AiBenchmarkService(db).update_benchmarks(payload)
