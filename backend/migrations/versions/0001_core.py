"""core: initial schema

Revision ID: 0001_core
Revises:
Create Date: 2026-11-10 00:00:00.000000
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        schema="core",
    )

    op.create_table(
        "identities",
        sa.Column("identity_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(120), nullable=True),
        sa.UniqueConstraint("provider", "external_id"),
        schema="core",
    )
    op.create_index("ix_identities_user_id", "identities", ["user_id"], schema="core")

    op.create_table(
        "device_secrets",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("secret_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="core",
    )

    op.create_table(
        "consents",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("kind", sa.String(32), primary_key=True),
        sa.Column("version", sa.String(32), primary_key=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="core",
    )

    op.create_table(
        "profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("current_version", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="core",
    )

    op.create_table(
        "profile_versions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("version", sa.Integer, primary_key=True),
        sa.Column("body", postgresql.JSONB, nullable=False),
        sa.Column("birth_date", sa.Date, nullable=True),
        sa.Column("completeness", sa.Numeric(4, 3), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="core",
    )

    op.create_table(
        "recommendation_runs",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_version", sa.Integer, nullable=False),
        sa.Column("strategy", sa.String(40), nullable=True),
        sa.Column("state", sa.String(16), server_default="queued", nullable=False),
        sa.Column("filters", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column("programme_prior", postgresql.JSONB, nullable=True),
        sa.Column("model_versions", postgresql.JSONB, nullable=True),
        sa.Column("catalog_watermark", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_candidates", sa.Integer, nullable=True),
        sa.Column("idempotency_key", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_runs_user_idem"),
        schema="core",
    )
    op.execute(
        "CREATE INDEX ix_runs_user_created ON core.recommendation_runs (user_id, created_at DESC)"
    )

    op.create_table(
        "recommendation_items",
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.recommendation_runs.run_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("programme_kind", sa.String(16), primary_key=True),
        sa.Column("rank", sa.Integer, primary_key=True),
        sa.Column("opportunity_id", sa.Integer, nullable=False),
        sa.Column("family_key", sa.String(120), nullable=True),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("breakdown", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column("reasons", postgresql.JSONB, server_default="[]", nullable=False),
        schema="core",
    )

    op.create_table(
        "feedback",
        sa.Column("feedback_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("opportunity_id", sa.Integer, nullable=False),
        sa.Column("signal", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="core",
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_feedback_sig "
        "ON core.feedback (user_id, opportunity_id, signal, run_id) NULLS NOT DISTINCT"
    )

    op.create_table(
        "subscriptions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("notify_new_matches", sa.Boolean, server_default=sa.true(), nullable=False),
        sa.Column("min_score", sa.Numeric(4, 3), server_default="0.7", nullable=False),
        sa.Column("channels", postgresql.ARRAY(sa.String(16)),
                  server_default=sa.text("ARRAY['telegram']::varchar[]"), nullable=False),
        sa.Column("last_notified_watermark", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="core",
    )

    op.create_table(
        "notification_outbox",
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger, nullable=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("state", sa.String(16), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer, server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dedupe_key", sa.String(120), nullable=False, unique=True),
        schema="core",
    )
    op.execute(
        "CREATE INDEX ix_outbox_state_lease ON core.notification_outbox (state, locked_until)"
    )

    op.create_table(
        "link_codes",
        sa.Column("code", sa.String(16), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("core.users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        schema="core",
    )


def downgrade() -> None:
    for t in (
        "link_codes", "notification_outbox", "subscriptions", "feedback",
        "recommendation_items", "recommendation_runs", "profile_versions",
        "profiles", "consents", "device_secrets", "identities", "users",
    ):
        op.drop_table(t, schema="core")