"""p4 persistence foundation

Revision ID: 0002_p4_persistence
Revises: 0001_baseline
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_p4_persistence"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("auto_sync_enabled", sa.Boolean(), nullable=False),
        sa.Column("auto_sync_frequency", sa.String(length=32), nullable=False),
        sa.Column("preferred_export_format", sa.String(length=16), nullable=False),
        sa.Column("preferred_units", sa.String(length=16), nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "athlete_profile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("gender", sa.String(length=80), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("age_years", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("training_focus", sa.String(length=500), nullable=True),
        sa.Column("experience_level", sa.String(length=32), nullable=True),
        sa.Column("notes_for_ai", sa.Text(), nullable=True),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=False),
        sa.Column("expires_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state"),
    )
    op.create_index(op.f("ix_oauth_states_provider"), "oauth_states", ["provider"], unique=False)
    op.create_index(op.f("ix_oauth_states_state"), "oauth_states", ["state"], unique=True)
    op.create_table(
        "whoop_connection",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("whoop_user_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("token_expires_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("granted_scopes", sa.Text(), nullable=True),
        sa.Column("connected_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_token_refresh_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("whoop_user_id", name="uq_whoop_connection_user"),
    )


def downgrade() -> None:
    op.drop_table("whoop_connection")
    op.drop_index(op.f("ix_oauth_states_state"), table_name="oauth_states")
    op.drop_index(op.f("ix_oauth_states_provider"), table_name="oauth_states")
    op.drop_table("oauth_states")
    op.drop_table("athlete_profile")
    op.drop_table("app_settings")

