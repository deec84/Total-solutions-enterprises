"""Add distributed authentication abuse-control state."""

import sqlalchemy as sa
from alembic import op

revision = "0009_distributed_login_rate_limit"
down_revision = "0008_parking_facilities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "login_rate_limits",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "failure_count > 0", name="ck_login_rate_limits_failure_count"
        ),
    )
    op.create_index(
        "ix_login_rate_limits_updated", "login_rate_limits", ["updated_at"]
    )


def downgrade() -> None:
    op.drop_table("login_rate_limits")
