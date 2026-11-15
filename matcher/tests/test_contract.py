"""Контракт POST /v1/match: что именно получает бэкенд (ТЗ-M раздел 3 и код backend/app/api/recommendations.py).

Если эти тесты красные, значит ответ матчера изменился так, что бэкенд может сломаться.
"""
from datetime import date

import pytest

from app.main import app
from tests.factories import make_opp

FEATURES = {"background", "skill", "language", "city", "duration", "cost", "chance", "freshness"}
REASON_CODES = {"background_match", "skill_match", "language_preferred", "city_pref",
                "duration_fit", "cost_fit", "chance_high", "chance_low", "fresh"}

# Ровно то тело, которое собирает бэкенд (recommendations.create_run)
BACKEND_PAYLOAD = {
    "request_id": "0b7f5c0e-6f4e-4d0e-9d39-5c1f0e3f5a11",
    "profile_id": "5f2b6c1e9a3d4e7f8a1b2c3d4e5f6a7b",
    "profile": {
        "programmes": ["talent"], "english_level": "B2",
        "study": {"status": "bachelor", "course": 3, "specialty_text": "Маркетинг"},
        "work_experience": "none", "spheres": ["marketing", "sales"], "activities": ["events"],
        "desired_countries": ["TR"], "duration": {"min_weeks": 6, "max_weeks": 12},
        "start_window": "asap",
        "financial": {"willing_to_pay": True, "max_budget_eur": 500, "needs_stipend": False},
    },
    "filters": {"programme_kinds": [], "country_codes": [], "exclude_opportunity_ids": []},
    "limit_per_programme": 10,
    "explain": True,
}


@pytest.fixture
def response(make_client):
    opps = [
        make_opp(1, title="Секретное название", backgrounds={10253: "required"}, skills={10161: "required"},
                 languages={10018: "required"}, duration_weeks=8, cost_total=0, date_opened=date.today(),
                 family_key="fam#1"),
        make_opp(2, backgrounds={99999: "required"}, family_key="fam#1"),
        make_opp(3, applicants_count=300, openings=1, available_openings=1),
    ]
    r = make_client(opps).post("/v1/match", json=BACKEND_PAYLOAD)
    assert r.status_code == 200, r.text
    return r.json()


def test_top_level_fields(response):
    assert set(response) == {"request_id", "profile_id", "strategy", "programme_prior",
                             "degraded", "took_ms", "groups"}
    assert response["request_id"] == BACKEND_PAYLOAD["request_id"]      # эхо для сквозной трассировки
    assert response["profile_id"] == BACKEND_PAYLOAD["profile_id"]
    assert response["strategy"] == "weighted_v1"
    assert response["programme_prior"] == {"talent": 1.0}
    assert isinstance(response["took_ms"], int) and response["took_ms"] >= 0

def test_group_fields_backend_reads(response):
    g = response["groups"][0]
    assert set(g) == {"programme_kind", "total_candidates", "items"}
    assert g["programme_kind"] == "talent" and g["total_candidates"] == 3

def test_item_fields_and_types(response):
    for it in response["groups"][0]["items"]:
        assert set(it) == {"opportunity_id", "rank", "score", "label", "reasons",
                           "breakdown", "family_key", "siblings_count"}
        assert isinstance(it["opportunity_id"], int)
        assert 0.0 <= it["score"] <= 1.0
        assert it["label"] in {"excellent", "good", "fair"}
        assert set(it["breakdown"]) == FEATURES
        assert all(0.0 <= v <= 1.0 for v in it["breakdown"].values())

def test_ranks_are_sequential_and_scores_descending(response):
    items = response["groups"][0]["items"]
    assert [i["rank"] for i in items] == list(range(1, len(items) + 1))
    assert [i["score"] for i in items] == sorted((i["score"] for i in items), reverse=True)

def test_family_collapsed_with_siblings_count(response):
    items = response["groups"][0]["items"]
    assert [i["opportunity_id"] for i in items] == [1, 3]               # 2 схлопнута в семью fam#1
    assert items[0]["siblings_count"] == 1 and items[0]["family_key"] == "fam#1"

def test_reasons_shape(response):
    for it in response["groups"][0]["items"]:
        pos = [r for r in it["reasons"] if r["polarity"] == "positive"]
        neg = [r for r in it["reasons"] if r["polarity"] == "negative"]
        assert len(pos) <= 3 and len(neg) <= 1                          # ТЗ-M 2.5
        for r in it["reasons"]:
            assert set(r) == {"code", "polarity", "weight", "text"}
            assert r["code"] in REASON_CODES and r["text"]

def test_no_reasons_when_explain_false(make_client):
    body = {**BACKEND_PAYLOAD, "explain": False}
    r = make_client([make_opp(1, cost_total=0)]).post("/v1/match", json=body)
    assert r.json()["groups"][0]["items"][0]["reasons"] == []

def test_response_has_no_vacancy_cards(response):
    # ТЗ-M: матчер отдаёт только id и оценки, карточку вакансии бэкенд берёт из catalog сам
    assert "Секретное название" not in str(response)

def test_same_request_gives_same_result(make_client):
    c = make_client([make_opp(i, applicants_count=i) for i in range(1, 30)])
    a = c.post("/v1/match", json=BACKEND_PAYLOAD).json()
    b = c.post("/v1/match", json=BACKEND_PAYLOAD).json()
    a.pop("took_ms"); b.pop("took_ms")
    assert a == b                                                       # ТЗ-M 2.8: детерминизм

def test_ties_ordered_by_opportunity_id(make_client):
    c = make_client([make_opp(i) for i in (9, 4, 7, 1)])
    items = c.post("/v1/match", json=BACKEND_PAYLOAD).json()["groups"][0]["items"]
    assert [i["opportunity_id"] for i in items] == [1, 4, 7, 9]

def test_openapi_describes_match():
    spec = app.openapi()
    post = spec["paths"]["/v1/match"]["post"]
    assert "200" in post["responses"] and "422" in post["responses"]
    props = spec["components"]["schemas"]["MatchRequest"]["properties"]
    assert {"profile", "filters", "limit_per_programme", "explain", "strategy"} <= set(props)
    assert props["limit_per_programme"]["minimum"] == 1 and props["limit_per_programme"]["maximum"] == 50

def test_openapi_paths_snapshot():
    # регрессия контракта: набор ручек не должен меняться случайно
    assert set(app.openapi()["paths"]) == {"/health", "/v1/match", "/dictionaries", "/dictionaries/{name}"}
