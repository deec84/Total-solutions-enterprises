"""Create geospatial parking risk zones."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0002_parking_zones"
down_revision: str | None = "0001_identity_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "parking_zones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column(
            "geometry",
            Geometry("POLYGON", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("parking_score", sa.Integer(), nullable=False),
        sa.Column("provenance", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("restriction_summary", sa.Text(), nullable=True),
        sa.Column("average_towing_cost_cents", sa.Integer(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "parking_score BETWEEN 0 AND 100", name="ck_parking_zones_score"
        ),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_parking_zones_confidence"),
        sa.CheckConstraint(
            "average_towing_cost_cents IS NULL OR average_towing_cost_cents >= 0",
            name="ck_parking_zones_towing_cost",
        ),
    )
    op.create_index(
        "ix_parking_zones_geometry",
        "parking_zones",
        ["geometry"],
        postgresql_using="gist",
    )
    op.create_index("ix_parking_zones_score", "parking_zones", ["parking_score"])


def downgrade() -> None:
    op.drop_table("parking_zones")
