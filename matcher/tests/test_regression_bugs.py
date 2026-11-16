"""Регрессионные тесты на найденные дефекты. Один тест = один баг-репорт.

До исправления тест красный (он и есть шаги воспроизведения).
После исправления его запускают отдельно (повторное тестирование),
а потом весь набор целиком (регрессионное тестирование).
"""
from datetime import date, timedelta

import pytest

from app import deps
from app.config import get_settings
from app.domain.features import freshness_score
from app.main import app
from fastapi.testclient import TestClient
from tests.factories import make_opp

P = {"programmes": ["talent"], "english_level": "B2"}


def _reset_caches():
    get_settings.cache_clear()
    for name in ("get_catalog_reader", "_build_reader"):
        fn = getattr(deps, name, None)
        if hasattr(fn, "cache_clear"):
            fn.cache_clear()

PAID = [make_opp(1, cost_total=300.0, cost_currency="EUR")]


def test_bug_m01_text_budget_is_422_not_500(make_client):
    """BUG-M-01: бюджет строкой 'abc' ронял сервис с 500."""
    r = make_client(PAID).post("/v1/match", json={"profile": {**P, "financial": {"max_budget_eur": "abc"}}})
    assert r.status_code == 422

def test_bug_m01_numeric_string_budget_works(make_client):
    """BUG-M-01: бюджет строкой '200' тоже давал 500; теперь это число 200."""
    r = make_client(PAID).post("/v1/match", json={"profile": {**P, "financial": {"max_budget_eur": "200"}}})
    assert r.status_code == 200 and r.json()["groups"][0]["items"] == []      # 300 > 200, отфильтрована

@pytest.mark.parametrize("study", [{"level": ["bachelor"]}, {"field": 5}, {"level": {"a": 1}}, "bachelor"])
def test_bug_m02_wrong_study_types_are_422(make_client, study):
    """BUG-M-02: study.level списком или study.field числом давали 500."""
    assert make_client(PAID).post("/v1/match", json={"profile": {**P, "study": study}}).status_code == 422

@pytest.mark.parametrize("days_ahead", [1, 30, 400])
def test_bug_m03_future_date_opened_is_not_fresher_than_today(days_ahead):
    """BUG-M-03: дата открытия в будущем давала свежесть больше 1."""
    o = make_opp(1, date_opened=date.today() + timedelta(days=days_ahead))
    assert freshness_score(o, date.today()) == 1.0

def test_bug_m03_score_never_above_one(make_client):
    """BUG-M-03: из-за свежести итоговая оценка получалась 5.13 при максимуме 1."""
    opp = make_opp(1, date_opened=date.today() + timedelta(days=400), backgrounds={10253: "required"},
                   skills={10161: "required"}, cost_total=0, duration_weeks=8)
    body = {"profile": {**P, "spheres": ["marketing", "sales"], "duration": {"min_weeks": 6, "max_weeks": 10}}}
    item = make_client([opp]).post("/v1/match", json=body).json()["groups"][0]["items"][0]
    assert item["score"] <= 1.0 and item["breakdown"]["freshness"] <= 1.0

def test_bug_m04_dictionaries_root_is_200(client):
    """BUG-M-04: GET /dictionaries отвечал 500."""
    r = client.get("/dictionaries")
    assert r.status_code == 200
    assert r.json() == ["backgrounds", "languages", "skills"]

def test_bug_m05_label_matches_shown_score(make_client):
    """BUG-M-05: оценка 0.74996 показывалась как 0.75, а метка была good вместо excellent."""
    from app.domain.scoring import rank_programme
    from tests.factories import make_profile
    from unittest.mock import patch
    feats = dict.fromkeys(["background", "skill", "language", "city", "duration", "cost", "chance", "freshness"], 0.74996)
    with patch("app.domain.scoring.compute_features", return_value=feats):
        item = rank_programme([make_opp(1)], make_profile(), "talent", set(), 10, False, 0.75, 0.55).items[0]
    assert item.score == 0.75 and item.label == "excellent"

@pytest.mark.parametrize("duration", [{"min_weeks": 12, "max_weeks": 6}, {"min_weeks": -5}, {"max_weeks": -1}])
def test_bug_m06_bad_duration_range_is_422(make_client, duration):
    """BUG-M-06: диапазон 'от 12 до 6 недель' и отрицательные недели принимались молча."""
    assert make_client(PAID).post("/v1/match", json={"profile": {**P, "duration": duration}}).status_code == 422

def test_bug_m07_nationality_code_case_insensitive(make_client):
    """BUG-M-07: 'ru' маленькими буквами молча игнорировалось, фильтр гражданства не работал."""
    c = make_client([make_opp(1, nationalities={10353})])               # только Азербайджан
    for code in ("RU", "ru", "Ru"):
        r = c.post("/v1/match", json={"profile": {**P, "nationality": code}})
        assert r.json()["groups"][0]["items"] == [], code

def test_bug_m07_language_code_case_insensitive(make_client):
    c = make_client([make_opp(1, languages={10043: "required"})])       # нужен русский
    for code in ("ru", "RU"):
        r = c.post("/v1/match", json={"profile": {**P, "other_languages": [code]}})
        assert len(r.json()["groups"][0]["items"]) == 1, code

@pytest.mark.parametrize("env", [
    {"MATCHER_CATALOG_SOURCE": "db", "MATCHER_DATABASE_URL": ""},
    {"MATCHER_CATALOG_SOURCE": "fake", "MATCHER_FAKE_CATALOG_PATH": "no_such_file.json"},
])
def test_bug_m09_broken_catalog_config_is_503(monkeypatch, env):
    """BUG-M-09: пустой адрес БД или отсутствующий файл каталога давали 500 вместо 503."""
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    _reset_caches()
    app.dependency_overrides.clear()
    try:
        r = TestClient(app, raise_server_exceptions=False).post("/v1/match", json={"profile": P})
        assert r.status_code == 503
        assert r.json()["detail"]["type"] == "catalog-unavailable"
    finally:
        monkeypatch.undo()
        _reset_caches()

def test_bug_m10_study_status_from_form_is_used(make_client):
    """BUG-M-10: анкета присылает study.status, а матчер читал только study.level,
    поэтому фильтр по уровню учёбы никогда не срабатывал."""
    c = make_client([make_opp(1, study_levels={10782})])                # только для школьников
    r = c.post("/v1/match", json={"profile": {**P, "study": {"status": "bachelor"}}})
    assert r.json()["groups"][0]["items"] == []
