"""Add parking classification and towing-hotspot flags."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_parking_zone_classification"
down_revision: str | None = "0002_parking_zones"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "parking_zones",
        sa.Column("zone_type", sa.String(32), nullable=False, server_default="general"),
    )
    op.add_column(
        "parking_zones",
        sa.Column("towing_hotspot", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_check_constraint(
        "ck_parking_zones_type",
        "parking_zones",
        "zone_type IN ('general', 'resident_only', 'private_property', "
        "'commercial', 'towing_hotspot')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_parking_zones_type", "parking_zones", type_="check")
    op.drop_column("parking_zones", "towing_hotspot")
    op.drop_column("parking_zones", "zone_type")
