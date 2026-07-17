"""Community reports with moderation and deduplication metadata."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_community_reports"
down_revision = "0003_parking_zone_classification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "community_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("validation_score", sa.Float(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("photo_sha256", sa.String(64), nullable=True),
        sa.Column("moderation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_community_reports_status_created",
        "community_reports",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_community_reports_fingerprint_created",
        "community_reports",
        ["fingerprint", "created_at"],
    )
    op.create_table(
        "reporter_reputations",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("approved_reports", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_reports", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "report_appeals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("appellant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["report_id"], ["community_reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["appellant_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_report_appeals_report_status", "report_appeals", ["report_id", "status"])


def downgrade() -> None:
    op.drop_table("report_appeals")
    op.drop_table("reporter_reputations")
    op.drop_table("community_reports")
