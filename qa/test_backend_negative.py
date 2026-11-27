"""Негативные и граничные проверки API бэкенда: права, проверка ввода, устойчивость к мусору."""
from datetime import date

import pytest

from conftest import API, BACKEND, PROFILE, QA_INTERNAL_TOKEN, User, new_email

pytestmark = pytest.mark.extended


def years_ago(n: int, plus_days: int = 0) -> str:
    t = date.today()
    try:
        d = t.replace(year=t.year - n)
    except ValueError:                       # 29 февраля
        d = t.replace(year=t.year - n, day=28)
    return date.fromordinal(d.toordinal() + plus_days).isoformat()


# ---------- доступ ----------
@pytest.mark.parametrize("method, path", [
    ("GET", "/me"), ("GET", "/profiles/me"), ("PUT", "/profiles/me"), ("POST", "/recommendations"),
    ("GET", "/recommendations/latest"), ("GET", "/history"), ("GET", "/analytics/me"),
    ("POST", "/feedback"), ("GET", "/feedback/liked"), ("GET", "/subscriptions/me"), ("DELETE", "/me"),
])
def test_private_endpoints_need_token(http, method, path):
    r = http.request(method, f"{API}{path}", json={})
    assert r.status_code in (401, 422)                         # 422 допустим, если тело проверяется раньше
    r = http.request(method, f"{API}{path}", json={}, headers={"Authorization": "Bearer not-a-token"})
    assert r.status_code in (401, 422)

@pytest.mark.parametrize("path", ["/me", "/profiles/me", "/history"])
def test_no_token_is_401_problem_json(http, path):
    r = http.get(f"{API}{path}")
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["type"] == "/problems/unauthorized"

def test_anonymous_auth_endpoint_is_removed(http):
    assert http.post(f"{API}/auth/anonymous", json={}).status_code == 404

def test_user_cannot_read_foreign_run(http, user, catalog):
    run_id = user.recommend().json()["run_id"]
    other = User(http, profile=PROFILE)
    assert other.get(f"/recommendations/{run_id}").status_code == 404
    other.delete("/me")


# ---------- регистрация и вход ----------
@pytest.mark.parametrize("password, ok", [
    ("Passw0r", False),            # 7 символов
    ("Passw0rd", True),            # 8 символов, граница
    ("p" * 127 + "1", True),       # 128 символов, граница
    ("p" * 128 + "1", False),      # 129 символов
    ("12345678", False),           # нет букв
    ("password", False),           # нет цифр
])
def test_password_rules(http, password, ok):
    r = http.post(f"{API}/auth/register", json={"email": new_email(), "password": password})
    assert r.status_code == (200 if ok else 422)

@pytest.mark.parametrize("email", ["", "no-at-sign", "a@b", "two@@example.com", "пробел @example.com"])
def test_bad_email_is_422(http, email):
    r = http.post(f"{API}/auth/register", json={"email": email, "password": "Passw0rd123"})
    assert r.status_code == 422 and r.json()["type"] == "/problems/validation"

def test_duplicate_email_is_409(http):
    email = new_email()
    assert http.post(f"{API}/auth/register", json={"email": email, "password": "Passw0rd123"}).status_code == 200
    r = http.post(f"{API}/auth/register", json={"email": email.upper(), "password": "Passw0rd123"})
    assert r.status_code == 409 and r.json()["type"] == "/problems/email-taken"

def test_wrong_password_and_unknown_user_look_the_same(http):
    email = new_email()
    http.post(f"{API}/auth/register", json={"email": email, "password": "Passw0rd123"})
    a = http.post(f"{API}/auth/login", json={"email": email, "password": "Wrong0000"})
    b = http.post(f"{API}/auth/login", json={"email": new_email(), "password": "Passw0rd123"})
    assert a.status_code == b.status_code == 401
    assert a.json()["title"] == b.json()["title"]              # нельзя угадать, есть ли такой пользователь


# ---------- анкета: границы возраста (18..31 включительно) ----------
@pytest.mark.parametrize("birth, ok", [
    (years_ago(18, plus_days=1), False),    # 18 исполнится завтра
    (years_ago(18), True),                  # 18 исполнилось сегодня
    (years_ago(32, plus_days=1), True),     # 32 исполнится завтра, пока 31
    (years_ago(32), False),                 # 32 исполнилось сегодня
    (years_ago(-1), False),                 # дата в будущем
    ("2003-02-30", False),                  # такой даты нет
])
def test_age_boundaries(user, birth, ok):
    r = user.put("/profiles/me", json={**PROFILE, "birth_date": birth})
    assert r.status_code == (200 if ok else 422), r.text

@pytest.mark.parametrize("patch", [
    {"english_level": "D1"}, {"programmes": ["intern"]}, {"work_experience": "100_years"},
    {"motivation_text": "я" * 1001}, {"experience_text": "я" * 2001}, {"city": "г" * 101},
    {"duration": {"min_weeks": "шесть"}}, {"preferred_lc_ids": ["x"]},
])
def test_profile_validation(user, patch):
    assert user.put("/profiles/me", json={**PROFILE, **patch}).status_code == 422

def test_text_length_boundaries_accepted(user):
    r = user.put("/profiles/me", json={**PROFILE, "motivation_text": "я" * 1000, "experience_text": "я" * 2000})
    assert r.status_code == 200

def test_body_over_64kb_is_413(user):
    r = user.put("/profiles/me", json={**PROFILE, "x": "a" * 70_000})
    assert r.status_code == 413


# ---------- подбор ----------
def test_recommendations_without_profile_is_404(http):
    u = User(http)
    r = u.recommend()
    assert r.status_code == 404 and r.json()["type"] == "/problems/profile-not-found"
    u.delete("/me")

def test_recommendations_incomplete_profile_is_409(http):
    u = User(http, profile={"programmes": ["talent"]})
    r = u.recommend()
    assert r.status_code == 409 and r.json()["type"] == "/problems/profile-incomplete"
    assert {e["loc"][-1] for e in r.json()["errors"]} == {"english_level", "study.status", "birth_date"}
    u.delete("/me")

@pytest.mark.parametrize("headers", [{}, {"Idempotency-Key": "short"}])
def test_idempotency_key_required(user, headers):
    assert user.post("/recommendations", json={}, headers=headers).status_code == 422

@pytest.mark.parametrize("limit, ok", [(0, False), (1, True), (30, True), (31, False)])
def test_limit_boundaries(user, catalog, limit, ok):
    r = user.recommend({"limit_per_programme": limit})
    assert r.status_code == (200 if ok else 422)

def test_unknown_programme_in_filters_is_422(user):
    r = user.recommend({"filters": {"programme_kinds": ["intern"]}})
    assert r.status_code == 422


# ---------- каталог ----------
@pytest.mark.parametrize("params, status", [
    ({"limit": 0}, 422), ({"limit": 1}, 200), ({"limit": 100}, 200), ({"limit": 101}, 422),
    ({"offset": -1}, 422), ({"sort": "random"}, 422), ({"lc_id": "abc"}, 422),
])
def test_opportunity_list_params(http, params, status):
    assert http.get(f"{API}/opportunities", params=params).status_code == status

def test_unknown_opportunity_is_404(http):
    r = http.get(f"{API}/opportunities/999999999")
    assert r.status_code == 404 and r.json()["type"] == "/problems/opportunity-not-found"

def test_sql_injection_in_search_is_harmless(http, catalog):
    r = http.get(f"{API}/opportunities", params={"q": "'; DROP TABLE parser.opportunities; --"})
    assert r.status_code == 200 and r.json()["total"] == 0
    assert http.get(f"{API}/opportunities", params={"q": "QA Sales"}).json()["total"] == 1

def test_feedback_validation(user):
    assert user.post("/feedback", json={"opportunity_id": 1, "signal": "loved"}).status_code == 422
    assert user.post("/feedback", json={"opportunity_id": "x", "signal": "liked"}).status_code == 422
    assert user.delete("/feedback/1", params={"signal": "loved"}).status_code == 422


# ---------- открытые дефекты: сервер отвечает 500 на неверный ввод ----------
@pytest.mark.bug
@pytest.mark.parametrize("path", ["/history", "/analytics/me"])
def test_bug_b01_bad_date_filter_is_422_not_500(user, path):
    """BUG-B-01: ?from=abc даёт 500 в истории и аналитике."""
    assert user.get(path, params={"from": "abc"}).status_code == 422

@pytest.mark.bug
def test_bug_b02_bad_run_id_in_feedback_is_422_not_500(user):
    """BUG-B-02: run_id не в формате UUID даёт 500."""
    r = user.post("/feedback", json={"opportunity_id": 1, "signal": "liked", "run_id": "abc"})
    assert r.status_code == 422

@pytest.mark.bug
def test_bug_b03_bad_filters_type_is_422_not_500(user):
    """BUG-B-03: filters.exclude_opportunity_ids числом вместо списка даёт 500."""
    assert user.recommend({"filters": {"exclude_opportunity_ids": 5}}).status_code == 422

@pytest.mark.bug
def test_bug_b04_internal_api_is_not_open(http):
    """BUG-B-04: служебные ручки /internal/v1/notifications/* отвечают без какой-либо авторизации."""
    r = http.post(f"{BACKEND}/internal/v1/notifications/lease")
    assert r.status_code in (401, 403)
    r = http.post(
        f"{BACKEND}/internal/v1/notifications/lease",
        headers={"X-Internal-Token": QA_INTERNAL_TOKEN},
    )
    assert r.status_code == 200

@pytest.mark.bug
def test_bug_b05_group_total_candidates_is_reported(user, catalog):
    """BUG-B-05: в ответе подбора total_candidates у группы всегда 0, strategy всегда null."""
    run = user.recommend().json()
    assert run["strategy"] == "weighted_v1"
    assert run["groups"] and run["groups"][0]["total_candidates"] >= 1

@pytest.mark.bug
def test_bug_b06_labels_use_thresholds_from_spec(user, catalog, http):
    """BUG-B-06: бэкенд пересчитывает метку по порогам 0.8/0.6, а в ТЗ-M и матчере пороги 0.75/0.55."""
    from conftest import MATCHER
    body = {"profile": {k: v for k, v in PROFILE.items() if k not in ("birth_date", "motivation_text")}}
    direct = {i["opportunity_id"]: i["label"]
              for i in http.post(f"{MATCHER}/v1/match", json=body).json()["groups"][0]["items"]}
    shown = {i["opportunity"]["opportunity_id"]: i["label"]
             for g in user.recommend().json()["groups"] for i in g["items"]}
    assert shown and shown == {k: direct[k] for k in shown}

@pytest.mark.bug
def test_bug_w01_dashboard_preferences_endpoint_exists(user):
    """BUG-W-01: веб вызывает /users/me/dashboard-preferences, а в бэкенде такой ручки нет (404)."""
    assert user.get("/users/me/dashboard-preferences").status_code == 200
