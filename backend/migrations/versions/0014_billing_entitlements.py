"""Add privacy-preserving subscription and billing-event ledgers."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014_billing_entitlements"
down_revision = "0013_municipal_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("subject_reference", sa.String(64), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("product_id", sa.String(200), nullable=False),
        sa.Column("entitlement", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("environment", sa.String(16), nullable=False),
        sa.Column("transaction_reference", sa.String(64), nullable=False),
        sa.Column("original_transaction_reference", sa.String(64), nullable=False),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("auto_renews", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "platform IN ('apple_app_store', 'google_play')",
            name="ck_billing_subscription_platform",
        ),
        sa.CheckConstraint(
            "entitlement IN ('premium')",
            name="ck_billing_subscription_entitlement",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'grace_period', 'paused', 'expired', 'revoked')",
            name="ck_billing_subscription_status",
        ),
        sa.CheckConstraint(
            "environment IN ('sandbox', 'production')",
            name="ck_billing_subscription_environment",
        ),
        sa.CheckConstraint(
            "expires_at IS NULL OR expires_at > purchased_at",
            name="ck_billing_subscription_expiry",
        ),
    )
    op.create_index(
        "ix_billing_subscriptions_user_verified",
        "billing_subscriptions",
        ["user_id", "verified_at"],
    )
    op.create_index(
        "uq_billing_subscription_original",
        "billing_subscriptions",
        ["platform", "environment", "original_transaction_reference"],
        unique=True,
    )
    op.create_table(
        "billing_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("billing_subscriptions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider_event_reference", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'grace_period', 'paused', 'expired', 'revoked')",
            name="ck_billing_event_status",
        ),
    )
    op.create_index(
        "ix_billing_events_subscription_occurred",
        "billing_events",
        ["subscription_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_billing_events_subscription_occurred", table_name="billing_events"
    )
    op.drop_table("billing_events")
    op.drop_index(
        "uq_billing_subscription_original", table_name="billing_subscriptions"
    )
    op.drop_index(
        "ix_billing_subscriptions_user_verified", table_name="billing_subscriptions"
    )
    op.drop_table("billing_subscriptions")
