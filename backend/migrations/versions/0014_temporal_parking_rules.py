"""Persist governed temporal parking rules and jurisdiction lineage."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014_temporal_parking_rules"
down_revision = "0014_billing_entitlements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("parking_zones", sa.Column("jurisdiction", sa.String(160), nullable=True))
    op.add_column(
        "parking_zones",
        sa.Column(
            "temporal_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "parking_zones",
        sa.Column(
            "temporal_schedule_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("parking_zones", "temporal_schedule_required")
    op.drop_column("parking_zones", "temporal_rules")
    op.drop_column("parking_zones", "jurisdiction")
