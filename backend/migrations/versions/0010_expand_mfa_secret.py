"""Store authenticated MFA ciphertext without truncation."""

import sqlalchemy as sa
from alembic import op

revision = "0010_expand_mfa_secret"
down_revision = "0009_distributed_login_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "mfa_secret",
        existing_type=sa.String(length=64),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "mfa_secret",
        existing_type=sa.Text(),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
