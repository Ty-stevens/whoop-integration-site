"""p5 canonical schema

Revision ID: 0003_p5_canonical
Revises: 0002_p4_persistence
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_p5_canonical"
down_revision: str | None = "0002_p4_persistence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("external_v1_id", sa.String(length=128), nullable=True),
        sa.Column("whoop_user_id", sa.String(length=128), nullable=True),
        sa.Column("external_created_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_updated_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone_offset_text", sa.String(length=16), nullable=True),
        sa.Column("local_start_date", sa.Date(), nullable=False),
        sa.Column("iso_week_start_date", sa.Date(), nullable=False),
        sa.Column("local_month_start_date", sa.Date(), nullable=False),
        sa.Column("sport_name", sa.String(length=120), nullable=True),
        sa.Column("score_state", sa.String(length=64), nullable=True),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("strain", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("average_hr", sa.Integer(), nullable=True),
        sa.Column("max_hr", sa.Integer(), nullable=True),
        sa.Column("percent_recorded", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("zone0_seconds", sa.Integer(), nullable=False),
        sa.Column("zone1_seconds", sa.Integer(), nullable=False),
        sa.Column("zone2_seconds", sa.Integer(), nullable=False),
        sa.Column("zone3_seconds", sa.Integer(), nullable=False),
        sa.Column("zone4_seconds", sa.Integer(), nullable=False),
        sa.Column("zone5_seconds", sa.Integer(), nullable=False),
        sa.Column("raw_payload_json", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("source_revision", sa.Integer(), nullable=False),
        sa.Column("imported_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "classification in ('cardio', 'strength', 'other', 'unknown')",
            name="ck_workouts_classification",
        ),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_workouts_duration_nonnegative"),
        sa.CheckConstraint("zone0_seconds >= 0", name="ck_workouts_zone0_nonnegative"),
        sa.CheckConstraint("zone1_seconds >= 0", name="ck_workouts_zone1_nonnegative"),
        sa.CheckConstraint("zone2_seconds >= 0", name="ck_workouts_zone2_nonnegative"),
        sa.CheckConstraint("zone3_seconds >= 0", name="ck_workouts_zone3_nonnegative"),
        sa.CheckConstraint("zone4_seconds >= 0", name="ck_workouts_zone4_nonnegative"),
        sa.CheckConstraint("zone5_seconds >= 0", name="ck_workouts_zone5_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", name="uq_workouts_external_id"),
    )
    for column in [
        "external_id",
        "whoop_user_id",
        "local_start_date",
        "iso_week_start_date",
        "local_month_start_date",
    ]:
        op.create_index(op.f(f"ix_workouts_{column}"), "workouts", [column], unique=False)

    op.create_table(
        "sleeps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("external_v1_id", sa.String(length=128), nullable=True),
        sa.Column("cycle_id", sa.String(length=128), nullable=True),
        sa.Column("whoop_user_id", sa.String(length=128), nullable=True),
        sa.Column("external_created_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_updated_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone_offset_text", sa.String(length=16), nullable=True),
        sa.Column("local_start_date", sa.Date(), nullable=False),
        sa.Column("iso_week_start_date", sa.Date(), nullable=False),
        sa.Column("local_month_start_date", sa.Date(), nullable=False),
        sa.Column("nap", sa.Boolean(), nullable=False),
        sa.Column("score_state", sa.String(length=64), nullable=True),
        sa.Column("sleep_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("sleep_performance", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("sleep_efficiency", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("raw_payload_json", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("source_revision", sa.Integer(), nullable=False),
        sa.Column("imported_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("sleep_duration_seconds >= 0", name="ck_sleeps_duration_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", name="uq_sleeps_external_id"),
    )
    for column in [
        "external_id",
        "cycle_id",
        "whoop_user_id",
        "local_start_date",
        "iso_week_start_date",
        "local_month_start_date",
    ]:
        op.create_index(op.f(f"ix_sleeps_{column}"), "sleeps", [column], unique=False)

    op.create_table(
        "recoveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cycle_id", sa.String(length=128), nullable=False),
        sa.Column("sleep_external_id", sa.String(length=128), nullable=True),
        sa.Column("whoop_user_id", sa.String(length=128), nullable=True),
        sa.Column("external_created_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_updated_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("iso_week_start_date", sa.Date(), nullable=False),
        sa.Column("local_month_start_date", sa.Date(), nullable=False),
        sa.Column("score_state", sa.String(length=64), nullable=True),
        sa.Column("recovery_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("hrv_ms", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("resting_hr", sa.Integer(), nullable=True),
        sa.Column("respiratory_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("skin_temp_celsius", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("spo2_percent", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("raw_payload_json", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("source_revision", sa.Integer(), nullable=False),
        sa.Column("imported_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cycle_id", name="uq_recoveries_cycle_id"),
    )
    for column in [
        "cycle_id",
        "sleep_external_id",
        "whoop_user_id",
        "local_date",
        "iso_week_start_date",
        "local_month_start_date",
    ]:
        op.create_index(op.f(f"ix_recoveries_{column}"), "recoveries", [column], unique=False)

    op.create_table(
        "goal_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("effective_from_date", sa.Date(), nullable=False),
        sa.Column("effective_to_date", sa.Date(), nullable=True),
        sa.Column("zone1_target_minutes", sa.Integer(), nullable=False),
        sa.Column("zone2_target_minutes", sa.Integer(), nullable=False),
        sa.Column("zone3_target_minutes", sa.Integer(), nullable=False),
        sa.Column("zone4_target_minutes", sa.Integer(), nullable=False),
        sa.Column("zone5_target_minutes", sa.Integer(), nullable=False),
        sa.Column("cardio_sessions_target", sa.Integer(), nullable=False),
        sa.Column("strength_sessions_target", sa.Integer(), nullable=False),
        sa.Column("created_reason", sa.String(length=240), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("zone1_target_minutes >= 0", name="ck_goal_zone1_nonnegative"),
        sa.CheckConstraint("zone2_target_minutes >= 0", name="ck_goal_zone2_nonnegative"),
        sa.CheckConstraint("zone3_target_minutes >= 0", name="ck_goal_zone3_nonnegative"),
        sa.CheckConstraint("zone4_target_minutes >= 0", name="ck_goal_zone4_nonnegative"),
        sa.CheckConstraint("zone5_target_minutes >= 0", name="ck_goal_zone5_nonnegative"),
        sa.CheckConstraint("cardio_sessions_target >= 0", name="ck_goal_cardio_nonnegative"),
        sa.CheckConstraint(
            "strength_sessions_target >= 0",
            name="ck_goal_strength_nonnegative",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_goal_profiles_effective_from_date"),
        "goal_profiles",
        ["effective_from_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_goal_profiles_effective_to_date"),
        "goal_profiles",
        ["effective_to_date"],
        unique=False,
    )

    op.create_table(
        "workout_annotations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workout_id", sa.Integer(), nullable=False),
        sa.Column("manual_classification", sa.String(length=32), nullable=True),
        sa.Column("manual_strength_split", sa.String(length=32), nullable=True),
        sa.Column("tag", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "manual_classification is null or manual_classification in "
            "('cardio', 'strength', 'other', 'unknown')",
            name="ck_workout_annotations_manual_classification",
        ),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workout_id", name="uq_workout_annotations_workout_id"),
    )
    op.create_index(
        op.f("ix_workout_annotations_workout_id"),
        "workout_annotations",
        ["workout_id"],
        unique=False,
    )

    op.create_table(
        "sync_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("last_successful_sync_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_window_start_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_window_end_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cursor_text", sa.Text(), nullable=True),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_type", name="uq_sync_state_resource_type"),
    )
    op.create_index(op.f("ix_sync_state_resource_type"), "sync_state", ["resource_type"])

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(length=32), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("window_start_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("window_end_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inserted_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("unchanged_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sync_runs_resource_type"), "sync_runs", ["resource_type"])


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_runs_resource_type"), table_name="sync_runs")
    op.drop_table("sync_runs")
    op.drop_index(op.f("ix_sync_state_resource_type"), table_name="sync_state")
    op.drop_table("sync_state")
    op.drop_index(op.f("ix_workout_annotations_workout_id"), table_name="workout_annotations")
    op.drop_table("workout_annotations")
    op.drop_index(op.f("ix_goal_profiles_effective_to_date"), table_name="goal_profiles")
    op.drop_index(op.f("ix_goal_profiles_effective_from_date"), table_name="goal_profiles")
    op.drop_table("goal_profiles")
    for column in [
        "local_month_start_date",
        "iso_week_start_date",
        "local_date",
        "whoop_user_id",
        "sleep_external_id",
        "cycle_id",
    ]:
        op.drop_index(op.f(f"ix_recoveries_{column}"), table_name="recoveries")
    op.drop_table("recoveries")
    for column in [
        "local_month_start_date",
        "iso_week_start_date",
        "local_start_date",
        "whoop_user_id",
        "cycle_id",
        "external_id",
    ]:
        op.drop_index(op.f(f"ix_sleeps_{column}"), table_name="sleeps")
    op.drop_table("sleeps")
    for column in [
        "local_month_start_date",
        "iso_week_start_date",
        "local_start_date",
        "whoop_user_id",
        "external_id",
    ]:
        op.drop_index(op.f(f"ix_workouts_{column}"), table_name="workouts")
    op.drop_table("workouts")

