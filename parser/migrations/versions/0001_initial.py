"""initial: raw.opportunities, raw.sync_runs, raw.sync_state + app.opportunities view

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

SCHEMA_RAW = "raw"
SCHEMA_APP = "app"


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
        schema=SCHEMA_RAW,
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
        schema=SCHEMA_RAW,
    )

    op.create_table(
        "sync_state",
        sa.Column("key", sa.String(50), primary_key=True),
        sa.Column("value", sa.Text()),
        schema=SCHEMA_RAW,
    )

    op.execute(f"""
        CREATE VIEW {SCHEMA_APP}.opportunities AS
        SELECT
            opportunity_id, title, status, current_status, programme_id, programme_name,
            home_mc_id, home_mc_name, home_lc_id, home_lc_name, host_lc_id, host_lc_name,
            location, organisation_id, organisation_name,
            openings, available_openings, applicants_count, accepted_count,
            date_opened, applications_close_date, earliest_start_date, latest_end_date,
            duration, experience_type, cost_total, cost_currency, remote_updated_at,
            skills, backgrounds, languages, study_levels, nationalities, skills_developments,
            is_open, close_reason, first_seen_at, last_seen_at, closed_at, updated_at
        FROM {SCHEMA_RAW}.opportunities
    """)

    # Права ролям, если они существуют (на sqlite/тестах ролей нет — блок no-op).
    # GRANT выполняется от владельца схемы (parser_writer), поэтому разрешён.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'backend_reader') THEN
                GRANT SELECT ON app.opportunities TO backend_reader;
            END IF;
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'backend_writer') THEN
                GRANT SELECT ON app.opportunities TO backend_writer;
            END IF;
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'parser_writer') THEN
                GRANT USAGE ON SCHEMA raw TO parser_writer;
                GRANT USAGE ON SCHEMA app TO parser_writer;
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO parser_writer;
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO parser_writer;
                GRANT SELECT ON app.opportunities TO parser_writer;
                ALTER DEFAULT PRIVILEGES IN SCHEMA raw
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO parser_writer;
                ALTER DEFAULT PRIVILEGES IN SCHEMA app
                    GRANT SELECT ON TABLES TO parser_writer;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute(f"DROP VIEW IF EXISTS {SCHEMA_APP}.opportunities")
    op.drop_table("sync_state", schema=SCHEMA_RAW)
    op.drop_table("sync_runs", schema=SCHEMA_RAW)
    op.drop_table("opportunities", schema=SCHEMA_RAW)