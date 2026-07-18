"""Persist governed community-photo lifecycle metadata."""

import sqlalchemy as sa
from alembic import op

revision = "0011_community_media_lifecycle"
down_revision = "0010_expand_mfa_secret"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "community_reports", sa.Column("photo_object_key", sa.String(512), nullable=True)
    )
    op.add_column(
        "community_reports", sa.Column("photo_content_type", sa.String(32), nullable=True)
    )
    op.add_column(
        "community_reports", sa.Column("photo_size_bytes", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "community_reports",
        sa.Column("photo_retained_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "community_reports",
        sa.Column("photo_deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_community_media_complete",
        "community_reports",
        "(photo_object_key IS NULL AND photo_content_type IS NULL "
        "AND photo_size_bytes IS NULL AND photo_retained_until IS NULL) OR "
        "(photo_object_key IS NOT NULL AND photo_content_type IS NOT NULL "
        "AND photo_size_bytes IS NOT NULL AND photo_retained_until IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_community_media_size",
        "community_reports",
        "photo_size_bytes IS NULL OR photo_size_bytes BETWEEN 1 AND 10485760",
    )
    op.create_check_constraint(
        "ck_community_media_type",
        "community_reports",
        "photo_content_type IS NULL OR "
        "photo_content_type IN ('image/jpeg', 'image/png', 'image/webp')",
    )
    op.create_check_constraint(
        "ck_community_media_deletion",
        "community_reports",
        "photo_deleted_at IS NULL OR photo_object_key IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_community_media_retention",
        "community_reports",
        "photo_retained_until IS NULL OR "
        "(photo_retained_until > created_at "
        "AND photo_retained_until <= created_at + INTERVAL '30 days')",
    )
    op.create_index(
        "ix_community_reports_media_retention",
        "community_reports",
        ["photo_retained_until"],
    )


def downgrade() -> None:
    op.drop_index("ix_community_reports_media_retention", table_name="community_reports")
    op.drop_constraint(
        "ck_community_media_retention", "community_reports", type_="check"
    )
    op.drop_constraint(
        "ck_community_media_deletion", "community_reports", type_="check"
    )
    op.drop_constraint("ck_community_media_type", "community_reports", type_="check")
    op.drop_constraint("ck_community_media_size", "community_reports", type_="check")
    op.drop_constraint("ck_community_media_complete", "community_reports", type_="check")
    op.drop_column("community_reports", "photo_deleted_at")
    op.drop_column("community_reports", "photo_retained_until")
    op.drop_column("community_reports", "photo_size_bytes")
    op.drop_column("community_reports", "photo_content_type")
    op.drop_column("community_reports", "photo_object_key")
