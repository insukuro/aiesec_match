"""missing scenarios: notifications.read_at, email verification flow, link-code

Revision ID: 0006_missing_scenarios
Revises: 0005_drop_anonymous
Create Date: 2026-11-21 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_missing_scenarios"
down_revision = "0005_drop_anonymous"
branch_labels = None
depends_on = None

SCHEMA = "core"


def upgrade() -> None:
    # 1. Прочитанность уведомлений (в приложении).
    op.add_column(
        "notification_outbox",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.execute(
        "CREATE INDEX ix_outbox_user_created "
        "ON core.notification_outbox (user_id, created_at DESC)"
    )

    # 2. Email-верификация: нужен id, чтобы верифицировать конкретную заявку.
    #    В 0002_auth PK был user_id, но по смыслу нужен отдельный id.
    op.execute("ALTER TABLE core.email_verifications DROP CONSTRAINT IF EXISTS email_verifications_pkey")
    op.execute("ALTER TABLE core.email_verifications ADD COLUMN IF NOT EXISTS verification_id UUID")
    op.execute("UPDATE core.email_verifications SET verification_id = gen_random_uuid() WHERE verification_id IS NULL")
    op.execute("ALTER TABLE core.email_verifications ALTER COLUMN verification_id SET NOT NULL")
    op.execute("ALTER TABLE core.email_verifications ADD PRIMARY KEY (verification_id)")
    op.execute(
        "CREATE UNIQUE INDEX uq_email_verifications_user "
        "ON core.email_verifications (user_id)"
    )

    # 3. Link-code: индекс для поиска по user_id.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_link_codes_user "
        "ON core.link_codes (user_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS core.ix_link_codes_user")
    op.execute("DROP INDEX IF EXISTS core.uq_email_verifications_user")
    op.execute("ALTER TABLE core.email_verifications DROP CONSTRAINT email_verifications_pkey")
    op.execute("ALTER TABLE core.email_verifications DROP COLUMN verification_id")
    op.execute("ALTER TABLE core.email_verifications ADD PRIMARY KEY (user_id)")
    op.execute("DROP INDEX IF EXISTS core.ix_outbox_user_created")
    op.drop_column("notification_outbox", "read_at", schema=SCHEMA)