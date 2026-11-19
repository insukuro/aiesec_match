"""drop anonymous mode

Revision ID: 0005_drop_anonymous
Revises: 0004_feedback_unique
Create Date: 2026-11-20 00:24:34.00300
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_drop_anonymous"
down_revision = "0004_feedback_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE core.users DROP COLUMN IF EXISTS is_anonymous")
    op.execute("DROP TABLE IF EXISTS core.device_secrets")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="core",
    )
    op.create_table(
        "device_secrets",
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("core.users.user_id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("secret_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="core",
    )