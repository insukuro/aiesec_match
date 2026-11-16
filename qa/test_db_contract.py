"""Контракт базы данных (ТЗ-DB): вью catalog.*_v1 и права ролей.

Бэкенд и матчер читают каталог только через эти вью. Если поменять колонку
или её смысл, оба сервиса сломаются молча, поэтому контракт проверяется тестом.
"""
import psycopg
import pytest

from conftest import connect

OPPORTUNITY_V1 = {
    "opportunity_id": "integer", "title": "text", "family_key": "text", "programme_id": "integer",
    "programme_kind": "text", "country_code": "character", "country_name": "character varying",
    "lc_id": "integer", "lc_name": "character varying", "location": "character varying",
    "organisation_id": "integer", "organisation_name": "character varying", "openings": "integer",
    "available_openings": "integer", "applicants_count": "integer", "accepted_count": "integer",
    "date_opened": "date", "applications_close_date": "date", "earliest_start_date": "date",
    "latest_end_date": "date", "duration_weeks": "integer", "experience_type": "character varying",
    "cost_total": "double precision", "cost_currency": "character varying", "is_open": "boolean",
    "close_reason": "character varying", "remote_updated_at": "timestamp without time zone",
    "first_seen_at": "timestamp without time zone", "last_seen_at": "timestamp without time zone",
    "updated_at": "timestamp without time zone",
}
REQUIREMENT_V1 = {"opportunity_id": "integer", "kind": "text", "constant_id": "integer",
                  "constant_name": "text", "parent_name": "text", "option": "text", "level": "integer"}
SYNC_STATE_V1 = {"committed_watermark": "timestamp without time zone",
                 "last_success_at": "timestamp without time zone", "rows_total": "bigint",
                 "rows_open": "bigint", "last_run_kind": "text"}


def columns(view: str) -> dict:
    with connect("matcher_writer") as conn:
        rows = conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'catalog' AND table_name = %s", (view,)).fetchall()
    return dict(rows)


def one(sql: str, *params, role: str = "matcher_writer"):
    with connect(role) as conn:
        return conn.execute(sql, params).fetchall()


# ---------- набор колонок и типы ----------
@pytest.mark.critical
@pytest.mark.parametrize("view, expected", [
    ("opportunity_v1", OPPORTUNITY_V1), ("opportunity_requirement_v1", REQUIREMENT_V1),
    ("sync_state_v1", SYNC_STATE_V1),
])
def test_view_columns_and_types(view, expected):
    assert columns(view) == expected

@pytest.mark.extended
def test_service_columns_are_not_published():
    assert not {"raw", "source_query"} & set(columns("opportunity_v1"))


# ---------- смысл колонок ----------
@pytest.mark.critical
@pytest.mark.parametrize("key, kind", [("volunteer", "volunteer"), ("ideal", "talent"), ("teacher", "teacher")])
def test_programme_kind_mapping(catalog, key, kind):
    assert one("SELECT programme_kind FROM catalog.opportunity_v1 WHERE opportunity_id = %s",
               catalog[key]) == [(kind,)]

@pytest.mark.critical
def test_family_key_strips_weeks_suffix(catalog):
    fk = one("SELECT family_key FROM catalog.opportunity_v1 WHERE opportunity_id = %s", catalog["ideal"])[0][0]
    assert fk == "QA Sales at Cooler Systems#2452"

@pytest.mark.critical
@pytest.mark.bug
def test_bug_db01_requirement_constant_id_is_dictionary_id(catalog):
    """BUG-DB-01: вью отдаёт номер строки-связки (178561793) вместо номера из справочника (10253)."""
    rows = one("SELECT kind, constant_id FROM catalog.opportunity_requirement_v1 "
               "WHERE opportunity_id = %s ORDER BY kind, constant_id", catalog["ideal"])
    assert rows == [("background", 10233), ("background", 10253),
                    ("language", 10018), ("language", 10043),
                    ("nationality", 10353), ("nationality", 10463),
                    ("skill", 10161), ("study_level", 10785)]

@pytest.mark.extended
@pytest.mark.bug
def test_bug_db01_requirement_name_is_filled(catalog):
    """BUG-DB-01: название требования пустое, потому что вью читает ключ name, а в данных constant_name."""
    rows = one("SELECT kind, constant_name FROM catalog.opportunity_requirement_v1 "
               "WHERE opportunity_id = %s AND kind IN ('skill', 'study_level') ORDER BY kind", catalog["ideal"])
    assert rows == [("skill", "Sales"), ("study_level", "Bachelor")]

@pytest.mark.critical
@pytest.mark.bug
def test_bug_db02_country_code_is_filled(catalog):
    """BUG-DB-02: country_code всегда пустой: вью читает raw.home_mc.iso_code, а парсер такого поля не запрашивает."""
    rows = one("SELECT opportunity_id, country_code FROM catalog.opportunity_v1 "
               "WHERE opportunity_id IN (%s, %s) ORDER BY 1", catalog["ideal"], catalog["volunteer"])
    assert rows == [(catalog["ideal"], "TR"), (catalog["volunteer"], "TN")]

@pytest.mark.extended
def test_requirement_option_values(catalog):
    rows = one("SELECT DISTINCT option FROM catalog.opportunity_requirement_v1 "
               "WHERE opportunity_id BETWEEN 9900000 AND 9900999")
    assert {r[0] for r in rows} <= {"required", "preferred", None}

@pytest.mark.extended
def test_sync_state_counts_rows(catalog):
    total, opened = one("SELECT rows_total, rows_open FROM catalog.sync_state_v1")[0]
    assert total >= 7 and opened >= 4 and opened < total

@pytest.mark.extended
@pytest.mark.bug
def test_bug_db03_last_success_at_follows_successful_sync():
    """BUG-DB-03: вью ищет запуски со статусом 'success', а парсер пишет 'ok', поэтому поле всегда пустое."""
    with connect("parser_writer") as conn:
        conn.execute("INSERT INTO parser.sync_runs (kind, status, started_at, finished_at) "
                     "VALUES ('full', 'ok', now(), now())")
        try:
            assert conn.execute("SELECT last_success_at FROM catalog.sync_state_v1").fetchone()[0] is not None
        finally:
            conn.rollback()                         # тестовую запись в базе не оставляем


# ---------- права ролей (ТЗ-DB: один писатель на схему, чужие схемы закрыты) ----------
@pytest.mark.critical
@pytest.mark.parametrize("role", ["matcher_writer", "backend_writer"])
def test_consumers_can_read_catalog(role, catalog):
    assert one("SELECT count(*) FROM catalog.opportunity_v1", role=role)[0][0] >= 7

@pytest.mark.extended
@pytest.mark.parametrize("role, sql", [
    ("matcher_writer", "SELECT count(*) FROM parser.opportunities"),      # сырые данные парсера
    ("matcher_writer", "SELECT value FROM parser.sync_state"),            # здесь лежат токены AIESEC
    ("backend_writer", "SELECT value FROM parser.sync_state"),
    ("matcher_writer", "SELECT count(*) FROM core.users"),                # данные пользователей
    ("matcher_writer", "SELECT count(*) FROM core.profile_versions"),
    ("parser_writer", "SELECT count(*) FROM core.users"),
    ("matcher_writer", "DELETE FROM catalog.opportunity_v1"),             # каталог только для чтения
    ("backend_writer", "UPDATE catalog.opportunity_v1 SET title = 'x'"),
    ("matcher_writer", "CREATE TABLE public.qa_x (i int)"),
    ("matcher_writer", "CREATE TABLE catalog.qa_x (i int)"),
])
def test_foreign_schemas_are_closed(role, sql):
    with connect(role) as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(sql)

@pytest.mark.extended
@pytest.mark.parametrize("role, timeout", [("matcher_writer", "5s"), ("backend_writer", "5s"), ("parser_writer", "1min")])
def test_statement_timeouts(role, timeout):
    assert one("SHOW statement_timeout", role=role)[0][0] == timeout
