from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import iso_week_start
from app.models.athlete_profile import AthleteProfileModel
from app.repositories.goals import GoalRepository
from app.repositories.sync import SyncRepository
from app.services.ai.types import AiContext
from app.services.metrics.current_week import CurrentWeekMetricsService
from app.services.metrics.six_month_report import SixMonthReportMetricsService


class AiContextBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def build(self) -> AiContext:
        current_week = CurrentWeekMetricsService(self.db).build(iso_week_start(date.today()))
        today = date.today()
        report = SixMonthReportMetricsService(self.db).build(today)
        goals = GoalRepository(self.db).history()[:5]
        sync_states = SyncRepository(self.db).get_states()
        profile = self.db.query(AthleteProfileModel).one_or_none()

        return {
            "schema_version": "ai-context-v1",
            "app": {
                "name": self.settings.app_name,
                "version": self.settings.app_version,
                "generated_at_utc": datetime.now(UTC).isoformat(),
            },
            "sync": {
                "last_successful_sync_at_utc": max(
                    (
                        state.last_successful_sync_at_utc.isoformat()
                        for state in sync_states
                        if state.last_successful_sync_at_utc is not None
                    ),
                    default=None,
                ),
                "resources": [state.resource_type for state in sync_states],
            },
            "current_week": {
                "week_start_date": current_week.week_start_date.isoformat(),
                "week_end_date": current_week.week_end_date.isoformat(),
                "total_training_seconds": current_week.total_training_seconds,
                "zones": [zone.__dict__ for zone in current_week.zones],
                "cardio_sessions": current_week.cardio_sessions.__dict__,
                "strength_sessions": current_week.strength_sessions.__dict__,
                "average_recovery_score": current_week.average_recovery_score,
                "average_daily_strain": current_week.average_daily_strain,
            },
            "six_month_report": {
                "range_start_date": report.range_start_date.isoformat(),
                "range_end_date": report.range_end_date.isoformat(),
                "monthly_summaries": [
                    {
                        "month_label": month.month_label,
                        "training_seconds": month.training_seconds,
                        "workout_count": month.workout_count,
                        "cardio_count": month.cardio_count,
                        "strength_count": month.strength_count,
                        "average_recovery_score": month.average_recovery_score,
                        "average_daily_strain": month.average_daily_strain,
                    }
                    for month in report.monthly_summaries
                ],
                "consistency": report.consistency_summary.__dict__,
            },
            "recent_goals": [
                {
                    "effective_from_date": goal.effective_from_date.isoformat(),
                    "zone1_target_minutes": goal.zone1_target_minutes,
                    "zone2_target_minutes": goal.zone2_target_minutes,
                    "zone3_target_minutes": goal.zone3_target_minutes,
                    "zone4_target_minutes": goal.zone4_target_minutes,
                    "zone5_target_minutes": goal.zone5_target_minutes,
                    "cardio_sessions_target": goal.cardio_sessions_target,
                    "strength_sessions_target": goal.strength_sessions_target,
                }
                for goal in goals
            ],
            "athlete_profile": _profile_context(profile) if profile else None,
        }


def _profile_context(profile: AthleteProfileModel) -> dict:
    return {
        "display_name": profile.display_name,
        "age_years": profile.age_years,
        "training_focus": profile.training_focus,
        "experience_level": profile.experience_level,
        "notes_for_ai": profile.notes_for_ai,
    }
