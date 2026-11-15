"""Негативные тесты: неверные данные и сбои. Сервис обязан ответить понятной ошибкой, а не упасть."""
import pytest

from app.deps import get_catalog_reader
from app.main import app
from tests.factories import BrokenReader, make_opp

OK_PROFILE = {"programmes": ["talent"], "english_level": "B2"}


@pytest.mark.parametrize("body", [
    {},                                                          # нет profile
    {"profile": None},
    {"profile": {"programmes": ["intern"]}},                     # неизвестная программа
    {"profile": {"programmes": "talent"}},                       # строка вместо списка
    {"profile": {**OK_PROFILE, "english_level": "Z9"}},          # уровня нет в CEFR
    {"profile": {**OK_PROFILE, "english_level": "b2"}},          # регистр важен
    {"profile": OK_PROFILE, "limit_per_programme": "many"},
    {"profile": OK_PROFILE, "limit_per_programme": -1},
    {"profile": OK_PROFILE, "explain": "maybe"},
    {"profile": OK_PROFILE, "filters": {"programme_kinds": ["intern"]}},
    {"profile": OK_PROFILE, "filters": {"exclude_opportunity_ids": ["abc"]}},
    {"profile": {**OK_PROFILE, "preferred_lc_ids": ["x"]}},
])
def test_invalid_body_is_422(client, body):
    assert client.post("/v1/match", json=body).status_code == 422

def test_not_json_is_422(client):
    r = client.post("/v1/match", content="это не json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422

def test_wrong_method_is_405(client):
    assert client.get("/v1/match").status_code == 405

def test_unknown_path_is_404(client):
    assert client.get("/v2/match").status_code == 404

def test_unknown_strategy_has_type(client):
    r = client.post("/v1/match", json={"profile": OK_PROFILE, "strategy": "magic"})
    assert r.status_code == 422
    assert r.json()["detail"]["type"] == "unknown-strategy"

def test_known_strategy_accepted(client):
    r = client.post("/v1/match", json={"profile": OK_PROFILE, "strategy": "weighted_v1"})
    assert r.status_code == 200 and r.json()["strategy"] == "weighted_v1"

def test_profile_incomplete_has_type_and_missing(client):
    r = client.post("/v1/match", json={"profile": {"english_level": "B2"}})
    assert r.status_code == 422
    assert r.json()["detail"] == {"type": "profile-incomplete", "missing": ["programmes"]}

def test_catalog_down_has_type(client):
    app.dependency_overrides[get_catalog_reader] = lambda: BrokenReader()
    r = client.post("/v1/match", json={"profile": OK_PROFILE})
    assert r.status_code == 503
    assert r.json()["detail"]["type"] == "catalog-unavailable"

def test_no_candidates_is_empty_group_not_error(make_client):
    c = make_client([])
    r = c.post("/v1/match", json={"profile": OK_PROFILE})
    assert r.status_code == 200
    assert r.json()["groups"] == [{"programme_kind": "talent", "total_candidates": 0, "items": []}]

def test_everything_filtered_out_is_empty_group(make_client):
    c = make_client([make_opp(1, cost_total=300.0)])
    r = c.post("/v1/match", json={"profile": {**OK_PROFILE, "financial": {"willing_to_pay": False}}})
    assert r.status_code == 200 and r.json()["groups"][0]["items"] == []

def test_excluded_ids_not_returned(make_client):
    c = make_client([make_opp(1), make_opp(2)])
    r = c.post("/v1/match", json={"profile": OK_PROFILE, "filters": {"exclude_opportunity_ids": [1]}})
    assert [i["opportunity_id"] for i in r.json()["groups"][0]["items"]] == [2]

def test_unknown_sphere_is_ignored_not_error(make_client):
    c = make_client([make_opp(1, backgrounds={10253: "required"})])
    r = c.post("/v1/match", json={"profile": {**OK_PROFILE, "spheres": ["космонавтика"]}})
    assert r.status_code == 200
    assert r.json()["groups"][0]["items"][0]["breakdown"]["background"] == 0.0

def test_huge_exclude_list_ok(make_client):
    c = make_client([make_opp(1)])
    r = c.post("/v1/match", json={"profile": OK_PROFILE,
                                  "filters": {"exclude_opportunity_ids": list(range(2, 5002))}})
    assert r.status_code == 200 and len(r.json()["groups"][0]["items"]) == 1

def test_dictionary_unknown_name_422(client):
    assert client.get("/dictionaries/passwords").status_code == 422

@pytest.mark.parametrize("name, size", [("skills", 309), ("backgrounds", 79), ("languages", 58)])
def test_dictionary_sizes(client, name, size):
    r = client.get(f"/dictionaries/{name}")
    assert r.status_code == 200 and len(r.json()) == size
    assert set(r.json()[0]) == {"id", "name"}                    # лишние поля наружу не отдаём
