"""catalog v1: исправление вью по результатам тестирования (BUG-DB-01, BUG-DB-02, BUG-DB-03)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-14
"""
from __future__ import annotations
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

SCHEMA = "parser"
CATALOG = "catalog"

KINDS = [("skill", "skills"), ("background", "backgrounds"), ("language", "languages"),
         ("study_level", "study_levels"), ("nationality", "nationalities"),
         ("skill_development", "skills_developments")]


def _requirement_view(id_expr: str, name_expr: str) -> str:
    union = "\n            UNION ALL\n".join(
        f"            SELECT opportunity_id, '{kind}' AS kind, "
        f"jsonb_array_elements(COALESCE(o.{col}, '[]'::jsonb)) AS el FROM {SCHEMA}.opportunities o"
        for kind, col in KINDS
    )
    return f"""
        CREATE OR REPLACE VIEW {CATALOG}.opportunity_requirement_v1 AS
        WITH expanded AS (
{union}
        )
        SELECT opportunity_id, kind,
               ({id_expr})::int       AS constant_id,
               {name_expr}            AS constant_name,
               el->>'parent_name'     AS parent_name,
               el->>'option'          AS option,
               (el->>'level')::int    AS level
        FROM expanded
        WHERE el IS NOT NULL
    """


def _opportunity_view(country_expr: str) -> str:
    return f"""
        CREATE OR REPLACE VIEW {CATALOG}.opportunity_v1 AS
        SELECT
            o.opportunity_id, o.title,
            (regexp_replace(o.title, '\\s*\\[\\d+\\s*weeks?\\]\\s*$', '', 'i')
                || '#' || COALESCE(o.host_lc_id::text, '0')) AS family_key,
            o.programme_id,
            CASE o.programme_id WHEN 7 THEN 'volunteer' WHEN 8 THEN 'talent' WHEN 9 THEN 'teacher' ELSE NULL END
                AS programme_kind,
            ({country_expr})::char(2) AS country_code,
            o.home_mc_name AS country_name, o.host_lc_id AS lc_id, o.host_lc_name AS lc_name, o.location,
            o.organisation_id, o.organisation_name, o.openings, o.available_openings,
            o.applicants_count, o.accepted_count, o.date_opened, o.applications_close_date,
            o.earliest_start_date, o.latest_end_date, o.duration AS duration_weeks, o.experience_type,
            o.cost_total, o.cost_currency, o.is_open, o.close_reason, o.remote_updated_at,
            o.first_seen_at, o.last_seen_at, o.updated_at
        FROM {SCHEMA}.opportunities o
    """


def _sync_state_view(statuses: str) -> str:
    return f"""
        CREATE OR REPLACE VIEW {CATALOG}.sync_state_v1 AS
        SELECT
            (SELECT MAX(COALESCE(updated_at, first_seen_at)) FROM {SCHEMA}.opportunities) AS committed_watermark,
            (SELECT MAX(finished_at) FROM {SCHEMA}.sync_runs WHERE status IN ({statuses})) AS last_success_at,
            (SELECT COUNT(*) FROM {SCHEMA}.opportunities)               AS rows_total,
            (SELECT COUNT(*) FROM {SCHEMA}.opportunities WHERE is_open) AS rows_open,
            COALESCE((SELECT value FROM {SCHEMA}.sync_state WHERE key = 'last_run_kind'),
                     (SELECT kind FROM {SCHEMA}.sync_runs ORDER BY started_at DESC LIMIT 1)) AS last_run_kind
    """


def upgrade() -> None:
    # BUG-DB-01: у навыков, образования, языков и гражданства справочный номер лежит в constant_id,
    # а в id лежит номер строки-связки. У study_levels справочный номер в id, название в name.
    op.execute(_requirement_view("COALESCE(el->>'constant_id', el->>'id')",
                                 "COALESCE(el->>'constant_name', el->>'name')"))
    # BUG-DB-02: парсер запрашивает у AIESEC home_mc.country_code, поля iso_code в raw нет.
    op.execute(_opportunity_view("COALESCE(o.raw->'home_mc'->>'iso_code', o.raw->'home_mc'->>'country_code')"))
    # BUG-DB-03: парсер пишет статус успешного запуска как 'ok'.
    op.execute(_sync_state_view("'ok', 'success'"))


def downgrade() -> None:
    op.execute(_requirement_view("el->>'id'", "el->>'name'"))
    op.execute(_opportunity_view("o.raw->'home_mc'->>'iso_code'"))
    op.execute(_sync_state_view("'success'"))
