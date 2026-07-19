"""Add consent history and pseudonymous data-rights records."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012_privacy_rights"
down_revision = "0011_community_media_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "privacy_consent_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(48), nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "purpose IN ('product_analytics', 'personalized_recommendations', "
            "'community_research')",
            name="ck_privacy_consent_purpose",
        ),
    )
    op.create_index(
        "ix_privacy_consent_user_purpose_occurred",
        "privacy_consent_events",
        ["user_id", "purpose", "occurred_at"],
    )
    op.create_table(
        "data_rights_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("subject_reference", sa.String(64), nullable=False),
        sa.Column("request_type", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "request_type IN ('export', 'deletion')", name="ck_data_rights_type"
        ),
        sa.CheckConstraint(
            "status IN ('processing', 'completed')", name="ck_data_rights_status"
        ),
        sa.CheckConstraint(
            "(status = 'processing' AND completed_at IS NULL) OR "
            "(status = 'completed' AND completed_at IS NOT NULL)",
            name="ck_data_rights_completion",
        ),
    )
    op.create_index(
        "ix_data_rights_subject_requested",
        "data_rights_requests",
        ["subject_reference", "requested_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_data_rights_subject_requested", table_name="data_rights_requests")
    op.drop_table("data_rights_requests")
    op.drop_index(
        "ix_privacy_consent_user_purpose_occurred",
        table_name="privacy_consent_events",
    )
    op.drop_table("privacy_consent_events")
