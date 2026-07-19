"""Add governed municipal sources, import batches, and record lineage."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0013_municipal_ingestion"
down_revision = "0012_privacy_rights"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "municipal_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("jurisdiction", sa.String(160), nullable=False),
        sa.Column("feed_kind", sa.String(32), nullable=False),
        sa.Column("data_format", sa.String(16), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("license_url", sa.String(1000), nullable=True),
        sa.Column("official", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("refresh_interval_minutes", sa.Integer(), nullable=False),
        sa.Column("stale_after_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "feed_kind IN ('parking_zones', 'parking_facilities')",
            name="ck_municipal_source_feed_kind",
        ),
        sa.CheckConstraint(
            "data_format IN ('geojson', 'csv')", name="ck_municipal_source_format"
        ),
        sa.CheckConstraint(
            "refresh_interval_minutes BETWEEN 5 AND 10080",
            name="ck_municipal_source_refresh",
        ),
        sa.CheckConstraint(
            "stale_after_minutes >= refresh_interval_minutes",
            name="ck_municipal_source_staleness",
        ),
        sa.CheckConstraint(
            "official = FALSE OR license_url IS NOT NULL",
            name="ck_municipal_source_official_license",
        ),
    )
    op.create_index(
        "ix_municipal_sources_jurisdiction", "municipal_sources", ["jurisdiction"]
    )
    op.create_index("ix_municipal_sources_enabled", "municipal_sources", ["enabled"])
    op.create_table(
        "municipal_import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("municipal_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("importer_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("input_count", sa.Integer(), nullable=False),
        sa.Column("accepted_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('committed', 'partial', 'rejected')",
            name="ck_municipal_batch_status",
        ),
        sa.CheckConstraint(
            "input_count >= 0 AND accepted_count >= 0 AND rejected_count >= 0 "
            "AND accepted_count + rejected_count = input_count",
            name="ck_municipal_batch_counts",
        ),
    )
    op.create_index(
        "uq_municipal_batch_source_digest",
        "municipal_import_batches",
        ["source_id", "content_sha256"],
        unique=True,
    )
    op.create_index(
        "ix_municipal_batches_source_received",
        "municipal_import_batches",
        ["source_id", "received_at"],
    )
    op.create_table(
        "municipal_quarantine",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("municipal_import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("record_index", sa.Integer(), nullable=False),
        sa.Column("record_sha256", sa.String(64), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("reason_detail", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("record_index >= -1", name="ck_municipal_quarantine_index"),
    )
    op.create_index(
        "ix_municipal_quarantine_batch", "municipal_quarantine", ["batch_id"]
    )

    for table_name in ("parking_zones", "parking_facilities"):
        op.add_column(
            table_name,
            sa.Column(
                "source_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("municipal_sources.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.add_column(
            table_name,
            sa.Column(
                "import_batch_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("municipal_import_batches.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.add_column(
            table_name, sa.Column("external_record_id", sa.String(160), nullable=True)
        )
        op.create_index(
            f"uq_{table_name}_source_external",
            table_name,
            ["source_id", "external_record_id"],
            unique=True,
        )


def downgrade() -> None:
    for table_name in ("parking_facilities", "parking_zones"):
        op.drop_index(f"uq_{table_name}_source_external", table_name=table_name)
        op.drop_column(table_name, "external_record_id")
        op.drop_column(table_name, "import_batch_id")
        op.drop_column(table_name, "source_id")
    op.drop_index("ix_municipal_quarantine_batch", table_name="municipal_quarantine")
    op.drop_table("municipal_quarantine")
    op.drop_index(
        "ix_municipal_batches_source_received", table_name="municipal_import_batches"
    )
    op.drop_index(
        "uq_municipal_batch_source_digest", table_name="municipal_import_batches"
    )
    op.drop_table("municipal_import_batches")
    op.drop_index("ix_municipal_sources_enabled", table_name="municipal_sources")
    op.drop_index("ix_municipal_sources_jurisdiction", table_name="municipal_sources")
    op.drop_table("municipal_sources")
