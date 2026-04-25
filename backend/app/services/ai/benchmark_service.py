import json
import logging
from datetime import UTC, date, datetime, timedelta
from json import JSONDecodeError

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import iso_week_start
from app.repositories.goals import GoalRepository
from app.schemas.ai import (
    AiBenchmarkProposal,
    AiBenchmarkUpdateRequest,
    AiBenchmarkUpdateResponse,
)
from app.schemas.goals import GoalProfileCreate, GoalProfileResponse
from app.services.ai.context_builder import AiContextBuilder
from app.services.ai.prompts import benchmark_update_prompt
from app.services.ai.provider import provider_from_settings
from app.services.ai.types import AiProviderError
from app.services.goal_service import GoalProfileError, GoalProfileService

logger = logging.getLogger("endurasync.ai.benchmarks")


class AiBenchmarkService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def update_benchmarks(
        self,
        request: AiBenchmarkUpdateRequest,
    ) -> AiBenchmarkUpdateResponse:
        generated_at = datetime.now(UTC)
        if not self.settings.ai_enabled:
            return AiBenchmarkUpdateResponse(
                status="disabled",
                generated_at_utc=generated_at,
                message="AI is disabled.",
            )

        setup_error = self.settings.ai_setup_error
        if setup_error:
            logger.warning("ai.benchmarks.setup_error message=%s", setup_error)
            return AiBenchmarkUpdateResponse(
                status="setup_error",
                generated_at_utc=generated_at,
                message=setup_error,
            )

        try:
            context = AiContextBuilder(self.db).build()
            context["benchmark_update"] = {
                "requested_apply": request.apply,
                "effective_from_date": (
                    request.effective_from_date.isoformat()
                    if request.effective_from_date
                    else _next_monday(date.today()).isoformat()
                ),
                "current_targets": _current_target_context(self.db),
            }
            result = provider_from_settings(self.settings).generate(
                benchmark_update_prompt(context),
                response_format={"type": "json_object"},
            )
            proposal = _parse_proposal(result.text)
        except (AiProviderError, ValueError, ValidationError) as exc:
            logger.warning("ai.benchmarks.failed error_type=%s", exc.__class__.__name__)
            return AiBenchmarkUpdateResponse(
                status="error",
                generated_at_utc=generated_at,
                message="AI benchmark update is unavailable.",
            )

        if not request.apply:
            logger.info("ai.benchmarks.proposed changes=%s", len(proposal.changes))
            return AiBenchmarkUpdateResponse(
                status="success",
                applied=False,
                proposal=proposal,
                generated_at_utc=generated_at,
                message="AI benchmark proposal generated. Review before applying.",
            )

        effective_from_date = request.effective_from_date or _next_monday(date.today())
        try:
            profile = GoalProfileService(self.db).create_profile(
                GoalProfileCreate(
                    effective_from_date=effective_from_date,
                    zone1_target_minutes=proposal.targets.zone1_target_minutes,
                    zone2_target_minutes=proposal.targets.zone2_target_minutes,
                    zone3_target_minutes=proposal.targets.zone3_target_minutes,
                    zone4_target_minutes=proposal.targets.zone4_target_minutes,
                    zone5_target_minutes=proposal.targets.zone5_target_minutes,
                    cardio_sessions_target=proposal.targets.cardio_sessions_target,
                    strength_sessions_target=proposal.targets.strength_sessions_target,
                    created_reason=_created_reason(proposal),
                ),
                created_source="ai_benchmark_update",
                ai_provenance_json=_provenance(
                    proposal=proposal,
                    generated_at=generated_at,
                    effective_from_date=effective_from_date,
                ),
            )
        except (GoalProfileError, ValidationError, ValueError) as exc:
            logger.warning("ai.benchmarks.apply_failed error_type=%s", exc.__class__.__name__)
            return AiBenchmarkUpdateResponse(
                status="error",
                applied=False,
                proposal=proposal,
                generated_at_utc=generated_at,
                message="AI proposal could not be applied to the benchmark profile.",
            )

        logger.info("ai.benchmarks.applied goal_profile_id=%s", profile.id)
        return AiBenchmarkUpdateResponse(
            status="success",
            applied=True,
            proposal=proposal,
            profile=GoalProfileResponse.model_validate(profile),
            generated_at_utc=generated_at,
            message="AI benchmark update applied.",
        )


def _parse_proposal(text: str) -> AiBenchmarkProposal:
    try:
        payload = json.loads(_extract_json_object(text))
    except JSONDecodeError as exc:
        raise ValueError("AI benchmark response was not valid JSON") from exc
    return AiBenchmarkProposal.model_validate(payload)


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("AI benchmark response did not include a JSON object")
    return stripped[start : end + 1]


def _current_target_context(db: Session) -> dict:
    active = GoalRepository(db).active_for_week(iso_week_start(date.today()))
    if active is None:
        return {
            "zone1_target_minutes": 0,
            "zone2_target_minutes": 150,
            "zone3_target_minutes": 0,
            "zone4_target_minutes": 0,
            "zone5_target_minutes": 0,
            "cardio_sessions_target": 3,
            "strength_sessions_target": 2,
        }
    return {
        "zone1_target_minutes": active.zone1_target_minutes,
        "zone2_target_minutes": active.zone2_target_minutes,
        "zone3_target_minutes": active.zone3_target_minutes,
        "zone4_target_minutes": active.zone4_target_minutes,
        "zone5_target_minutes": active.zone5_target_minutes,
        "cardio_sessions_target": active.cardio_sessions_target,
        "strength_sessions_target": active.strength_sessions_target,
    }


def _next_monday(value: date) -> date:
    days_until_monday = (7 - value.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return value + timedelta(days=days_until_monday)


def _created_reason(proposal: AiBenchmarkProposal) -> str:
    return f"AI benchmark update: {proposal.summary}"[:240]


def _provenance(
    *,
    proposal: AiBenchmarkProposal,
    generated_at: datetime,
    effective_from_date: date,
) -> dict:
    return {
        "schema_version": "ai-benchmark-provenance-v1",
        "generated_at_utc": generated_at.isoformat(),
        "effective_from_date": effective_from_date.isoformat(),
        "provider": "openai_compatible",
        "model": get_settings().effective_ai_model,
        "summary": proposal.summary,
        "confidence": proposal.confidence,
        "changes": [change.model_dump() for change in proposal.changes],
    }
