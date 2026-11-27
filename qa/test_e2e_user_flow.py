"""Сквозной сценарий пользователя через бэкенд: регистрация -> согласие -> анкета -> подбор -> отклик.

Это критический путь: если он красный, продукт не работает, даже когда все модульные тесты зелёные.
"""
import uuid

import pytest

from conftest import API, MATCHER, PROFILE, User, consent_version

pytestmark = pytest.mark.critical


def ids(run: dict) -> list[int]:
    return [it["opportunity"]["opportunity_id"] for g in run["groups"] for it in g["items"]]


def test_register_login_me(http):
    u = User(http, with_consent=False)
    me = u.get("/me").json()
    assert me["email"] == u.email and me["has_profile"] is False
    r = http.post(f"{API}/auth/login", json={"email": u.email.upper(), "password": u.password})
    assert r.status_code == 200 and r.json()["access_token"]           # почта без учёта регистра
    u.delete("/me")

def test_profile_requires_consent_then_saves(bare_user):
    r = bare_user.put("/profiles/me", json=PROFILE)
    assert r.status_code == 403 and r.json()["type"] == "/problems/consent-required"
    assert bare_user.post(
        "/me/consents",
        json={
            "kind": "pd_processing",
            "version": consent_version(bare_user.http),
        },
    ).status_code == 204
    r = bare_user.put("/profiles/me", json=PROFILE)
    assert r.status_code == 200
    body = r.json()
    assert body["profile_version"] == 1 and body["age_years"] >= 18 and 0 < body["completeness"] <= 1
    assert r.headers["ETag"] == '"1"'
    assert bare_user.get("/profiles/me").json()["spheres"] == ["marketing", "sales"]

def test_profile_versions_and_conflict(user):
    r = user.put("/profiles/me", json={**PROFILE, "english_level": "C1"}, headers={"If-Match": '"1"'})
    assert r.status_code == 200 and r.json()["profile_version"] == 2
    r = user.put("/profiles/me", json=PROFILE, headers={"If-Match": '"1"'})        # устаревшая версия
    assert r.status_code == 412 and r.json()["type"] == "/problems/version-conflict"
    assert [v["version"] for v in user.get("/profiles/me/versions").json()] == [2, 1]
    assert user.get("/profiles/me/versions/1").json()["english_level"] == "B2"

@pytest.mark.bug
def test_recommendations_return_matching_opportunity(user, catalog):
    """Главный сценарий. Сейчас красный из-за BUG-DB-01 (а при MATCHER_CATALOG_SOURCE=fake из-за заглушки)."""
    r = user.recommend()
    assert r.status_code == 200, r.text
    run = r.json()
    assert run["state"] == "succeeded" and run["programme_prior"] == ["talent"]
    found = ids(run)
    assert catalog["ideal"] in found
    assert not {catalog["closed"], catalog["full"], catalog["expired"]} & set(found)
    assert not {catalog["volunteer"], catalog["teacher"]} & set(found)             # другие программы
    top = run["groups"][0]["items"][0]
    assert top["opportunity"]["opportunity_id"] == catalog["ideal"]
    assert top["opportunity"]["title"].startswith("QA Sales")
    assert 0 <= top["score"] <= 1 and top["label"] in {"excellent", "good", "fair"}
    assert top["reasons"], "у лучшей вакансии должны быть объяснения"

def test_recommendations_are_idempotent(user, catalog):
    key = str(uuid.uuid4())
    a, b = user.recommend(key=key).json(), user.recommend(key=key).json()
    assert a["run_id"] == b["run_id"]
    assert user.get(f"/recommendations/{a['run_id']}").json()["run_id"] == a["run_id"]
    assert user.get("/recommendations/latest").json()["run_id"] == a["run_id"]

@pytest.mark.bug
def test_hidden_opportunity_disappears_from_next_run(user, catalog):
    assert catalog["ideal"] in ids(user.recommend().json())
    assert user.post("/feedback", json={"opportunity_id": catalog["ideal"], "signal": "hidden"}).status_code == 204
    assert catalog["ideal"] not in ids(user.recommend().json())

def test_feedback_like_and_unlike(user, catalog):
    oid = catalog["weak"]
    for _ in range(2):                                                             # повтор не создаёт дубль
        assert user.post("/feedback", json={"opportunity_id": oid, "signal": "liked"}).status_code == 204
    liked = user.get("/feedback/liked").json()
    assert liked["total"] == 1 and liked["items"][0]["opportunity_id"] == oid
    assert user.delete(f"/feedback/{oid}", params={"signal": "liked"}).status_code == 204
    assert user.get("/feedback/liked").json()["total"] == 0

def test_history_and_analytics_after_run(user, catalog):
    user.recommend()
    user.post("/feedback", json={"opportunity_id": catalog["weak"], "signal": "liked"})
    types = {e["type"] for e in user.get("/history").json()["items"]}
    assert {"run_finished", "signal_liked"} <= types
    a = user.get("/analytics/me", params={"period": "7d"}).json()
    assert a["profile_completeness"]["percent"] > 50
    assert a["activity_series"] and a["activity_series"][-1]["run_started"] >= 1

def test_opportunity_list_and_card(http, catalog):
    page = http.get(f"{API}/opportunities", params={"q": "QA Sales", "limit": 5}).json()
    assert page["total"] == 1 and page["items"][0]["opportunity_id"] == catalog["ideal"]
    card = http.get(f"{API}/opportunities/{catalog['ideal']}").json()
    assert card["programme"]["kind"] == "talent" and card["capacity"]["available_openings"] == 3
    assert http.get(f"{API}/opportunities", params={"q": "QA closed"}).json()["total"] == 0
    assert http.get(f"{API}/opportunities", params={"q": "QA closed", "only_open": "false"}).json()["total"] == 1

@pytest.mark.bug
def test_bug_db02_country_filter_finds_opportunities(http, catalog):
    """BUG-DB-02: фильтр по стране ничего не находит, потому что country_code пустой."""
    page = http.get(f"{API}/opportunities", params={"country_code": "TN", "q": "QA"}).json()
    assert [i["opportunity_id"] for i in page["items"]] == [catalog["volunteer"]]

@pytest.mark.bug
def test_bug_db01_card_shows_requirement_names(http, catalog):
    """BUG-DB-01: в карточке вакансии названия требований пустые (name: null)."""
    reqs = http.get(f"{API}/opportunities/{catalog['ideal']}").json()["requirements"]
    assert {r["name"] for r in reqs if r["kind"] == "skill"} == {"Sales"}

def test_subscription_roundtrip(user):
    assert user.get("/subscriptions/me").json()["min_score"] == 0.7
    body = {"notify_new_matches": False, "min_score": 0.85, "channels": ["telegram"]}
    assert user.put("/subscriptions/me", json=body).json() == body
    assert user.get("/subscriptions/me").json() == body

def test_account_deletion_revokes_access(http, catalog):
    u = User(http, profile=PROFILE)
    u.recommend()
    assert u.delete("/me").status_code == 204
    assert u.get("/me").status_code == 401                              # токен удалённого пользователя не работает
    r = http.post(f"{API}/auth/login", json={"email": u.email, "password": u.password})
    assert r.status_code == 401

def test_matcher_and_backend_agree_on_top_item(user, catalog, http):
    """Интеграция backend -> matcher: бэкенд показывает то же, что посчитал матчер."""
    body = {"profile": {k: v for k, v in PROFILE.items() if k not in ("birth_date", "motivation_text")},
            "filters": {}, "limit_per_programme": 10}
    direct = http.post(f"{MATCHER}/v1/match", json=body).json()["groups"][0]["items"]
    via_backend = user.recommend().json()["groups"]
    if not direct:                                                      # пустой подбор ловит другой тест
        pytest.skip("матчер ничего не нашёл, см. test_recommendations_return_matching_opportunity")
    assert via_backend[0]["items"][0]["opportunity"]["opportunity_id"] == direct[0]["opportunity_id"]
    assert via_backend[0]["items"][0]["score"] == pytest.approx(direct[0]["score"], abs=1e-4)
