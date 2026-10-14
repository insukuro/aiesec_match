"""Тесты HTTP-ручек через TestClient. AIESEC подменён FakeClient, БД — временный sqlite."""
from collections import Counter
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import main
from app.models import Base

from .conftest import TODAY, FakeClient, make_row

ROWS = [
    make_row(1, mc=1559, title="Marketing in Tunis"),
    make_row(2, mc=1609, title="Software in Cairo"),
    make_row(3, mc=1622, lc=941, title="Teaching in Adana"),
    make_row(4, mc=1559, close=TODAY + timedelta(days=2), title="Design in Tunis"),
]


@pytest.fixture
def api(monkeypatch):
    engine = main.SessionLocal.kw["bind"]
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    fake = FakeClient([dict(r) for r in ROWS])
    monkeypatch.setattr(main.service, "client", fake)
    monkeypatch.setattr(main, "client", fake)
    monkeypatch.setattr(main.settings, "api_key", None)
    with TestClient(main.app) as c:
        yield SimpleNamespace(c=c, fake=fake)


@pytest.fixture
def seeded(api):
    main.service._full(Counter())
    return api


# ---------------- служебные ----------------
def test_health(api):
    j = api.c.get("/health").json()
    assert j == {"status": "ok", "sync_running": False, "scheduler": False,
                 "aiesec_auth": "ok"}


def test_api_key_required_when_configured(api, monkeypatch):
    monkeypatch.setattr(main.settings, "api_key", "secret")
    assert api.c.get("/opportunities").status_code == 401
    assert api.c.get("/opportunities", headers={"X-API-Key": "wrong"}).status_code == 401
    assert api.c.get("/opportunities", headers={"X-API-Key": "secret"}).status_code == 200
    assert api.c.get("/health").status_code == 200  # health без ключа


# ---------------- чтение ----------------
def test_list_and_shape(seeded):
    j = seeded.c.get("/opportunities").json()
    assert j["total"] == 4
    item = j["items"][0]
    assert "opportunity_id" in item and "id" not in item
    assert "raw" not in item  # тяжёлое поле только в карточке


def test_filters(seeded):
    ids = lambda **p: {i["opportunity_id"] for i in seeded.c.get("/opportunities", params=p).json()["items"]}
    assert ids(country="tunisia") == {1, 4}            # регистронезависимо
    assert ids(city="Adana") == {3}
    assert ids(q="Cairo") == {2}
    assert ids(closing_before=(TODAY + timedelta(days=3)).isoformat()) == {4}
    assert ids(new_since="2999-01-01T00:00:00") == set()
    assert seeded.c.get("/opportunities", params={"country": "Atlantis"}).status_code == 404
    assert seeded.c.get("/opportunities", params={"city": "Paris"}).status_code == 404


def test_pagination_and_sorting(seeded):
    j = seeded.c.get("/opportunities", params={"limit": 2, "offset": 2}).json()
    assert j["total"] == 4 and len(j["items"]) == 2
    first = seeded.c.get("/opportunities", params={"sort": "applications_close_date", "desc": "false"}).json()
    assert first["items"][0]["opportunity_id"] == 4    # самый ранний дедлайн
    assert seeded.c.get("/opportunities", params={"limit": 9999}).status_code == 422


def test_stats(seeded):
    j = seeded.c.get("/opportunities/stats").json()
    assert j["open_total"] == 4
    assert j["countries"]["Tunisia"] == 2 and j["countries"]["Egypt"] == 1
    assert j["turkey_cities"]["Adana"] == 1 and j["turkey_cities"]["Konya"] == 0
    assert j["last_full_at"]


def test_detail(seeded):
    j = seeded.c.get("/opportunities/1").json()
    assert j["opportunity_id"] == 1 and j["raw"]["id"] == "1"
    assert seeded.c.get("/opportunities/999").status_code == 404


# ---------------- refresh ----------------
def test_refresh_closes_and_hides_from_default_list(seeded):
    next(r for r in seeded.fake.remote if r["id"] == "2")["status"] = "closed"
    j = seeded.c.post("/opportunities/2/refresh").json()
    assert j["result"] == "closed" and j["opportunity"]["is_open"] is False
    assert seeded.c.get("/opportunities").json()["total"] == 3
    assert seeded.c.get("/opportunities", params={"only_open": "false"}).json()["total"] == 4


def test_refresh_501_when_single_getter_missing(seeded):
    seeded.fake.single_getter = False
    assert seeded.c.post("/opportunities/1/refresh").status_code == 501


# ---------------- синхронизация ----------------
def test_trigger_full_sync_end_to_end(api):
    r = api.c.post("/sync/full")
    assert r.status_code == 202 and r.json()["kind"] == "full"
    assert api.c.get("/opportunities").json()["total"] == 4
    runs = api.c.get("/sync/runs").json()
    assert runs[0]["status"] == "ok" and runs[0]["stats"]["inserted"] == 4


def test_unknown_sync_kind_rejected(api):
    assert api.c.post("/sync/everything").status_code == 422


def test_concurrent_sync_returns_409(api):
    run_id = main.service.try_start("full")
    try:
        assert api.c.post("/sync/incremental").status_code == 409
        assert api.c.get("/health").json()["sync_running"] is True
    finally:
        main.service.execute(run_id, "full")
    assert api.c.post("/sync/incremental").status_code == 202


def test_failed_sync_is_visible_in_runs(api):
    api.fake.fail_on_page = 1
    api.c.post("/sync/full")
    run = api.c.get("/sync/runs").json()[0]
    assert run["status"] == "failed" and "simulated outage" in run["error"]


def test_expire_endpoint(seeded):
    assert seeded.c.post("/maintenance/expire").json() == {"closed": 0}


# ---------------- админка ----------------
def test_admin_endpoints(api):
    assert api.c.get("/admin/targets").json()["countries"]["Tunisia"] == 1559
    assert api.c.get("/admin/offices", params={"q": "tun"}).json()[0]["tag"] == "MC"
    assert api.c.get("/admin/offices", params={"q": "t"}).status_code == 422
    f = api.c.get("/admin/schema/filters").json()
    assert "home_mcs" in f["filters"] and f["incremental_filter_ok"] is True