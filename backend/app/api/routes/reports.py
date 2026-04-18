import csv
from dataclasses import asdict
from datetime import date
from io import StringIO
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.deps import DbSession
from app.schemas.reports import SixMonthReportResponse
from app.services.metrics.six_month_report import SixMonthReportMetricsService

router = APIRouter()
AsOfDateQuery = Annotated[date | None, Query()]


@router.get("/six-month", response_model=SixMonthReportResponse)
def six_month_report(
    db: DbSession,
    as_of_date: AsOfDateQuery = None,
) -> SixMonthReportResponse:
    summary = SixMonthReportMetricsService(db).build(as_of_date or date.today())
    return SixMonthReportResponse.model_validate(asdict(summary))


@router.get("/six-month/export.csv")
def six_month_report_export(
    db: DbSession,
    as_of_date: AsOfDateQuery = None,
) -> Response:
    summary = SixMonthReportMetricsService(db).build(as_of_date or date.today())
    return Response(
        content=_render_csv(summary),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; "
                f'filename="six-month-report-{summary.range_start_date}_to_'
                f'{summary.range_end_date}.csv"'
            )
        },
    )


def _render_csv(summary) -> str:
    buffer = StringIO()
    fieldnames = [
        "range_start_date",
        "range_end_date",
        "month_start_date",
        "month_end_date",
        "month_label",
        "workout_count",
        "sleep_count",
        "recovery_count",
        "training_seconds",
        "zone1_minutes",
        "zone2_minutes",
        "zone3_minutes",
        "zone4_minutes",
        "zone5_minutes",
        "cardio_count",
        "strength_count",
        "other_count",
        "unknown_count",
        "average_recovery_score",
        "average_daily_strain",
        "weeks_in_range",
        "active_weeks",
        "weeks_with_workouts",
        "weeks_with_sleeps",
        "weeks_with_recoveries",
        "training_week_coverage_percent",
        "sleep_week_coverage_percent",
        "recovery_week_coverage_percent",
        "summary_text",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for month in summary.monthly_summaries:
        writer.writerow(
            {
                "range_start_date": summary.range_start_date,
                "range_end_date": summary.range_end_date,
                "month_start_date": month.month_start_date,
                "month_end_date": month.month_end_date,
                "month_label": month.month_label,
                "workout_count": month.workout_count,
                "sleep_count": month.sleep_count,
                "recovery_count": month.recovery_count,
                "training_seconds": month.training_seconds,
                "zone1_minutes": month.zone1_minutes,
                "zone2_minutes": month.zone2_minutes,
                "zone3_minutes": month.zone3_minutes,
                "zone4_minutes": month.zone4_minutes,
                "zone5_minutes": month.zone5_minutes,
                "cardio_count": month.cardio_count,
                "strength_count": month.strength_count,
                "other_count": month.other_count,
                "unknown_count": month.unknown_count,
                "average_recovery_score": month.average_recovery_score,
                "average_daily_strain": month.average_daily_strain,
                "weeks_in_range": summary.consistency_summary.weeks_in_range,
                "active_weeks": summary.consistency_summary.active_weeks,
                "weeks_with_workouts": summary.consistency_summary.weeks_with_workouts,
                "weeks_with_sleeps": summary.consistency_summary.weeks_with_sleeps,
                "weeks_with_recoveries": summary.consistency_summary.weeks_with_recoveries,
                "training_week_coverage_percent": (
                    summary.consistency_summary.training_week_coverage_percent
                ),
                "sleep_week_coverage_percent": (
                    summary.consistency_summary.sleep_week_coverage_percent
                ),
                "recovery_week_coverage_percent": (
                    summary.consistency_summary.recovery_week_coverage_percent
                ),
                "summary_text": summary.consistency_summary.summary_text,
            }
        )
    return buffer.getvalue()
