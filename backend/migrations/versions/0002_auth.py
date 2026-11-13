"""auth: password_credentials, password_reset_tokens, email_verifications

Revision ID: 0002_auth
Revises: 0001_core
Create Date: 2026-11-11
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_auth"
down_revision = "0001_core"
branch_labels = None
depends_on = None

SCHEMA = "core"


def upgrade() -> None:
    op.create_table(
        "password_credentials",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey(f"{SCHEMA}.users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=SCHEMA,
    )
    op.create_index("ix_password_credentials_email", "password_credentials", ["email"], schema=SCHEMA)

    op.create_table(
        "password_reset_tokens",
        sa.Column("token_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey(f"{SCHEMA}.users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=SCHEMA,
    )
    op.create_index("ix_password_reset_user", "password_reset_tokens", ["user_id"], schema=SCHEMA)

    op.create_table(
        "email_verifications",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey(f"{SCHEMA}.users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("email_verifications", schema=SCHEMA)
    op.drop_index("ix_password_reset_user", table_name="password_reset_tokens", schema=SCHEMA)
    op.drop_table("password_reset_tokens", schema=SCHEMA)
    op.drop_index("ix_password_credentials_email", table_name="password_credentials", schema=SCHEMA)
    op.drop_table("password_credentials", schema=SCHEMA)