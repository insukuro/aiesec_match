"""initial: parser.opportunities, parser.sync_runs, parser.sync_state

Revision ID: 0001
Revises:
Create Date: 2026-10-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = "parser"


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("opportunity_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("title", sa.Text()),
        sa.Column("status", sa.String(50)),
        sa.Column("current_status", sa.String(50)),
        sa.Column("programme_id", sa.Integer(), index=True),
        sa.Column("programme_name", sa.String(100)),
        sa.Column("home_mc_id", sa.Integer(), index=True),
        sa.Column("home_mc_name", sa.String(200)),
        sa.Column("home_lc_id", sa.Integer(), index=True),
        sa.Column("home_lc_name", sa.String(200)),
        sa.Column("host_lc_id", sa.Integer(), index=True),
        sa.Column("host_lc_name", sa.String(200)),
        sa.Column("location", sa.String(300)),
        sa.Column("organisation_id", sa.Integer()),
        sa.Column("organisation_name", sa.String(300)),
        sa.Column("openings", sa.Integer()),
        sa.Column("available_openings", sa.Integer()),
        sa.Column("applicants_count", sa.Integer()),
        sa.Column("accepted_count", sa.Integer()),
        sa.Column("date_opened", sa.Date()),
        sa.Column("applications_close_date", sa.Date(), index=True),
        sa.Column("earliest_start_date", sa.Date()),
        sa.Column("latest_end_date", sa.Date()),
        sa.Column("duration", sa.Integer()),
        sa.Column("experience_type", sa.String(100)),
        sa.Column("cost_total", sa.Float()),
        sa.Column("cost_currency", sa.String(10)),
        sa.Column("remote_updated_at", sa.DateTime(), index=True),
        sa.Column("skills", postgresql.JSONB()),
        sa.Column("backgrounds", postgresql.JSONB()),
        sa.Column("languages", postgresql.JSONB()),
        sa.Column("study_levels", postgresql.JSONB()),
        sa.Column("nationalities", postgresql.JSONB()),
        sa.Column("skills_developments", postgresql.JSONB()),
        sa.Column("raw", postgresql.JSONB()),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("close_reason", sa.String(50)),
        sa.Column("source_query", sa.String(50)),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema=SCHEMA,
    )

    op.create_table(
        "sync_runs",
        sa.Column("run_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("stats", postgresql.JSONB()),
        sa.Column("error", sa.Text()),
        schema=SCHEMA,
    )

    op.create_table(
        "sync_state",
        sa.Column("key", sa.String(50), primary_key=True),
        sa.Column("value", sa.Text()),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("sync_state", schema=SCHEMA)
    op.drop_table("sync_runs", schema=SCHEMA)
    op.drop_table("opportunities", schema=SCHEMA)