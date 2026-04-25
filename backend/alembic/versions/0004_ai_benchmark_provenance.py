"""ai benchmark provenance

Revision ID: 0004_ai_benchmark_provenance
Revises: 0003_p5_canonical
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_ai_benchmark_provenance"
down_revision: str | None = "0003_p5_canonical"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    existing_columns = {
        column["name"] for column in sa.inspect(op.get_bind()).get_columns("goal_profiles")
    }
    if "created_source" not in existing_columns:
        op.add_column(
            "goal_profiles",
            sa.Column(
                "created_source",
                sa.String(length=32),
                nullable=False,
                server_default="manual",
            ),
        )
    if "ai_provenance_json" not in existing_columns:
        op.add_column("goal_profiles", sa.Column("ai_provenance_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("goal_profiles", "ai_provenance_json")
    op.drop_column("goal_profiles", "created_source")
