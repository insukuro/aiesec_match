"""catalog v1: opportunity_v1, opportunity_requirement_v1, sync_state_v1

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-11
"""
from __future__ import annotations
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SCHEMA = "parser"
CATALOG = "catalog"


def upgrade() -> None:
    # 4.1 catalog.opportunity_v1
    op.execute(f"""
        CREATE OR REPLACE VIEW {CATALOG}.opportunity_v1 AS
        SELECT
            o.opportunity_id,
            o.title,
            (regexp_replace(o.title, '\\s*\\[\\d+\\s*weeks?\\]\\s*$', '', 'i')
                || '#' || COALESCE(o.host_lc_id::text, '0')) AS family_key,
            o.programme_id,
            CASE o.programme_id
                WHEN 7 THEN 'volunteer'
                WHEN 8 THEN 'talent'
                WHEN 9 THEN 'teacher'
                ELSE NULL
            END AS programme_kind,
            (o.raw->'home_mc'->>'iso_code')::char(2) AS country_code,
            o.home_mc_name AS country_name,
            o.host_lc_id AS lc_id,
            o.host_lc_name AS lc_name,
            o.location,
            o.organisation_id,
            o.organisation_name,
            o.openings,
            o.available_openings,
            o.applicants_count,
            o.accepted_count,
            o.date_opened,
            o.applications_close_date,
            o.earliest_start_date,
            o.latest_end_date,
            o.duration AS duration_weeks,
            o.experience_type,
            o.cost_total,
            o.cost_currency,
            o.is_open,
            o.close_reason,
            o.remote_updated_at,
            o.first_seen_at,
            o.last_seen_at,
            o.updated_at
        FROM {SCHEMA}.opportunities o
    """)

    # 4.2 catalog.opportunity_requirement_v1
    op.execute(f"""
        CREATE OR REPLACE VIEW {CATALOG}.opportunity_requirement_v1 AS
        WITH expanded AS (
            SELECT opportunity_id, 'skill' AS kind,
                   jsonb_array_elements(COALESCE(o.skills, '[]'::jsonb)) AS el
            FROM {SCHEMA}.opportunities o
            UNION ALL
            SELECT opportunity_id, 'background',
                   jsonb_array_elements(COALESCE(o.backgrounds, '[]'::jsonb))
            FROM {SCHEMA}.opportunities o
            UNION ALL
            SELECT opportunity_id, 'language',
                   jsonb_array_elements(COALESCE(o.languages, '[]'::jsonb))
            FROM {SCHEMA}.opportunities o
            UNION ALL
            SELECT opportunity_id, 'study_level',
                   jsonb_array_elements(COALESCE(o.study_levels, '[]'::jsonb))
            FROM {SCHEMA}.opportunities o
            UNION ALL
            SELECT opportunity_id, 'nationality',
                   jsonb_array_elements(COALESCE(o.nationalities, '[]'::jsonb))
            FROM {SCHEMA}.opportunities o
            UNION ALL
            SELECT opportunity_id, 'skill_development',
                   jsonb_array_elements(COALESCE(o.skills_developments, '[]'::jsonb))
            FROM {SCHEMA}.opportunities o
        )
        SELECT
            opportunity_id,
            kind,
            (el->>'id')::int          AS constant_id,
            el->>'name'               AS constant_name,
            el->>'parent_name'        AS parent_name,
            el->>'option'             AS option,
            (el->>'level')::int       AS level
        FROM expanded
        WHERE el IS NOT NULL
    """)

    # 4.3 catalog.sync_state_v1
    op.execute(f"""
        CREATE OR REPLACE VIEW {CATALOG}.sync_state_v1 AS
        SELECT
            (SELECT MAX(COALESCE(updated_at, first_seen_at))
               FROM {SCHEMA}.opportunities)                          AS committed_watermark,
            (SELECT MAX(finished_at)
               FROM {SCHEMA}.sync_runs
              WHERE status = 'success')                              AS last_success_at,
            (SELECT COUNT(*) FROM {SCHEMA}.opportunities)            AS rows_total,
            (SELECT COUNT(*) FROM {SCHEMA}.opportunities
              WHERE is_open)                                         AS rows_open,
            COALESCE(
                (SELECT value FROM {SCHEMA}.sync_state
                  WHERE key = 'last_run_kind'),
                (SELECT kind FROM {SCHEMA}.sync_runs
                  ORDER BY started_at DESC LIMIT 1)
            )                                                        AS last_run_kind
    """)


def downgrade() -> None:
    op.execute(f"DROP VIEW IF EXISTS {CATALOG}.sync_state_v1")
    op.execute(f"DROP VIEW IF EXISTS {CATALOG}.opportunity_requirement_v1")
    op.execute(f"DROP VIEW IF EXISTS {CATALOG}.opportunity_v1")