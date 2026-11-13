"""feedback: один сигнал каждого типа на (user, opportunity)

Старый индекс включал run_id, а run_id может быть NULL, что приводило
к дубликатам и к невозможности «отменить» сигнал.

Revision ID: 0004_feedback_unique
Revises: 0003_auth
Create Date: 2026-11-14
"""
from __future__ import annotations

from alembic import op

revision = "0004_feedback_unique"
down_revision = "0003_auth"
branch_labels = None
depends_on = None

SCHEMA = "core"


def upgrade() -> None:
    # Удаляем старый (с run_id) и создаём новый unique-индекс.
    op.execute("DROP INDEX IF EXISTS core.uq_feedback_sig")
    # Перед созданием чистим дубликаты (берём минимальный created_at).
    op.execute(f"""
        DELETE FROM {SCHEMA}.feedback f
        USING {SCHEMA}.feedback g
        WHERE f.ctid > g.ctid
          AND f.user_id = g.user_id
          AND f.opportunity_id = g.opportunity_id
          AND f.signal = g.signal
    """)
    op.execute(f"""
        CREATE UNIQUE INDEX uq_feedback_sig
        ON {SCHEMA}.feedback (user_id, opportunity_id, signal)
    """)
    # Индекс для быстрого выбора по сигналу.
    op.execute(f"""
        CREATE INDEX IF NOT EXISTS ix_feedback_user_signal
        ON {SCHEMA}.feedback (user_id, signal)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS core.ix_feedback_user_signal")
    op.execute("DROP INDEX IF EXISTS core.uq_feedback_sig")
    op.execute("""
        CREATE UNIQUE INDEX uq_feedback_sig
        ON core.feedback (user_id, opportunity_id, signal, run_id)
        NULLS NOT DISTINCT
    """)