"""auth: users.is_anonymous + password_credentials (email уже unique)

Revision ID: 0003_auth
Revises: 0002_auth
Create Date: 2026-11-12
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "0003_auth"
down_revision = "0002_auth"
branch_labels = None
depends_on = None

SCHEMA = "core"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("users", "is_anonymous", schema=SCHEMA)