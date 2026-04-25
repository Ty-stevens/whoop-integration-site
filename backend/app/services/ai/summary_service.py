import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import iso_week_start
from app.repositories.goals import GoalRepository
from app.schemas.ai import (
    AiGoalSuggestion,
    AiGoalSuggestionsResponse,
    AiWeeklySummaryResponse,
)
from app.services.ai.context_builder import AiContextBuilder
from app.services.ai.prompts import goal_suggestions_prompt, weekly_summary_prompt
from app.services.ai.provider import provider_from_settings
from app.services.ai.types import AiProviderError

logger = logging.getLogger("endurasync.ai.summary")


class AiSummaryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def weekly_summary(self) -> AiWeeklySummaryResponse:
        generated_at = datetime.now(UTC)
        if not self.settings.ai_enabled:
            return AiWeeklySummaryResponse(
                status="disabled",
                generated_at_utc=generated_at,
                message="AI is disabled.",
            )
        if self.settings.ai_setup_error:
            return AiWeeklySummaryResponse(
                status="error",
                generated_at_utc=generated_at,
                message=self.settings.ai_setup_error,
            )
        try:
            context = AiContextBuilder(self.db).build()
            result = provider_from_settings(self.settings).generate(weekly_summary_prompt(context))
        except AiProviderError:
            logger.warning("ai.summary.weekly_unavailable")
            return AiWeeklySummaryResponse(
                status="error",
                generated_at_utc=generated_at,
                message="AI summary is unavailable.",
            )
        observations = [
            line.strip("- ").strip() for line in result.text.splitlines() if line.strip()
        ]
        return AiWeeklySummaryResponse(
            status="success",
            summary=result.text,
            observations=observations,
            generated_at_utc=generated_at,
            message="AI summary generated.",
        )

    def goal_suggestions(self) -> AiGoalSuggestionsResponse:
        generated_at = datetime.now(UTC)
        if not self.settings.ai_enabled:
            return AiGoalSuggestionsResponse(
                status="disabled",
                generated_at_utc=generated_at,
                message="AI is disabled.",
            )
        if self.settings.ai_setup_error:
            return AiGoalSuggestionsResponse(
                status="error",
                generated_at_utc=generated_at,
                message=self.settings.ai_setup_error,
            )
        try:
            context = AiContextBuilder(self.db).build()
            provider_from_settings(self.settings).generate(goal_suggestions_prompt(context))
        except AiProviderError:
            logger.warning("ai.summary.goal_suggestions_unavailable")
            return AiGoalSuggestionsResponse(
                status="error",
                generated_at_utc=generated_at,
                message="AI goal suggestions are unavailable.",
            )

        active = GoalRepository(self.db).active_for_week(iso_week_start(datetime.now(UTC).date()))
        if active is None:
            return AiGoalSuggestionsResponse(
                status="success",
                suggestions=[],
                generated_at_utc=generated_at,
                message="Create a goal profile before requesting AI goal suggestions.",
            )

        return AiGoalSuggestionsResponse(
            status="success",
            suggestions=[
                AiGoalSuggestion(
                    zone1_target_minutes=active.zone1_target_minutes,
                    zone2_target_minutes=active.zone2_target_minutes,
                    zone3_target_minutes=active.zone3_target_minutes,
                    zone4_target_minutes=active.zone4_target_minutes,
                    zone5_target_minutes=active.zone5_target_minutes,
                    cardio_sessions_target=active.cardio_sessions_target,
                    strength_sessions_target=active.strength_sessions_target,
                    rationale="Draft only. Review the provider summary before accepting changes.",
                    confidence="medium",
                )
            ],
            generated_at_utc=generated_at,
            message="AI returned advisory goal context. Accepting still uses the normal goal API.",
        )
