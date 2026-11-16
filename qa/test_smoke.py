"""Дымовой уровень: все части сервиса подняты и видят друг друга. Запускается первым."""
import pytest

from conftest import API, MATCHER, PARSER, connect

pytestmark = pytest.mark.smoke


def test_backend_alive(http):
    assert http.get(f"{API}/health").json() == {"status": "ok"}

def test_backend_sees_database(http):
    assert http.get(f"{API}/ready").json() == {"status": "ready"}

def test_matcher_alive(http):
    assert http.get(f"{MATCHER}/health").json() == {"status": "ok"}

def test_parser_alive(http):
    j = http.get(f"{PARSER}/health").json()
    assert j["status"] == "ok" and "aiesec_auth" in j

def test_database_has_all_schemas():
    with connect("parser_writer") as conn:
        names = {r[0] for r in conn.execute("SELECT nspname FROM pg_namespace")}
    assert {"parser", "catalog", "core", "matcher"} <= names

def test_form_schema_served(http):
    r = http.get(f"{API}/meta/form-schema")
    assert r.status_code == 200 and r.json()["steps"]

def test_matcher_answers_main_request(http):
    r = http.post(f"{MATCHER}/v1/match", json={"profile": {"programmes": ["talent"], "english_level": "B2"}})
    assert r.status_code == 200 and r.json()["groups"][0]["programme_kind"] == "talent"
