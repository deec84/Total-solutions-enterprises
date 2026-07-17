"""Add nearby parking facilities for explainable recommendations."""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision = "0008_parking_facilities"
down_revision = "0007_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parking_facilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column(
            "location",
            Geography("POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("hourly_price_cents", sa.Integer(), nullable=True),
        sa.Column("safety_score", sa.Integer(), nullable=False),
        sa.Column("towing_incidents_per_1000", sa.Float(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("available_spaces", sa.Integer(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("navigation_url", sa.String(1000), nullable=False),
        sa.Column("provenance", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "hourly_price_cents IS NULL OR hourly_price_cents >= 0",
            name="ck_parking_facilities_price",
        ),
        sa.CheckConstraint(
            "safety_score BETWEEN 0 AND 100",
            name="ck_parking_facilities_safety",
        ),
        sa.CheckConstraint(
            "towing_incidents_per_1000 >= 0",
            name="ck_parking_facilities_towing",
        ),
        sa.CheckConstraint(
            "rating IS NULL OR rating BETWEEN 0 AND 5",
            name="ck_parking_facilities_rating",
        ),
        sa.CheckConstraint(
            "available_spaces IS NULL OR available_spaces >= 0",
            name="ck_parking_facilities_available",
        ),
        sa.CheckConstraint(
            "capacity IS NULL OR capacity > 0",
            name="ck_parking_facilities_capacity",
        ),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ck_parking_facilities_confidence",
        ),
    )
    op.create_index(
        "ix_parking_facilities_location",
        "parking_facilities",
        ["location"],
        postgresql_using="gist",
    )
    op.create_index(
        "ix_parking_facilities_safety", "parking_facilities", ["safety_score"]
    )


def downgrade() -> None:
    op.drop_table("parking_facilities")
