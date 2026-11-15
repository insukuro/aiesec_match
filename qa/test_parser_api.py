"""Парсер как чёрный ящик: только чтение из его базы, без обращений к AIESEC.

Синхронизацию (POST /sync/...) здесь не запускаем: она ходит во внешний сервис
и расходует настоящий токен. Логику синхронизации проверяют модульные тесты парсера.
"""
import pytest

from conftest import PARSER

pytestmark = pytest.mark.extended


def test_list_shape(http, catalog):
    j = http.get(f"{PARSER}/opportunities", params={"q": "QA Sales"}).json()
    assert j["total"] == 1
    item = j["items"][0]
    assert item["opportunity_id"] == catalog["ideal"] and "raw" not in item

def test_only_open_by_default(http, catalog):
    ids = lambda **p: {i["opportunity_id"] for i in http.get(f"{PARSER}/opportunities", params={"q": "QA", "limit": 500, **p}).json()["items"]}
    assert catalog["closed"] not in ids() and catalog["expired"] not in ids()
    assert catalog["closed"] in ids(only_open="false")

def test_detail_and_404(http, catalog):
    assert http.get(f"{PARSER}/opportunities/{catalog['ideal']}").json()["raw"]["id"] == str(catalog["ideal"])
    assert http.get(f"{PARSER}/opportunities/999999999").status_code == 404

@pytest.mark.parametrize("params, status", [
    ({"limit": 0}, 422), ({"limit": 1}, 200), ({"limit": 500}, 200), ({"limit": 501}, 422),
    ({"offset": -1}, 422), ({"sort": "title"}, 422), ({"country": "Atlantis"}, 404), ({"city": "Paris"}, 404),
    ({"closing_before": "not-a-date"}, 422), ({"programme_id": "x"}, 422),
])
def test_list_params(http, params, status):
    assert http.get(f"{PARSER}/opportunities", params=params).status_code == status

def test_filter_by_programme(http, catalog):
    ids = {i["opportunity_id"] for i in http.get(f"{PARSER}/opportunities", params={"q": "QA", "programme_id": 7}).json()["items"]}
    assert ids == {catalog["volunteer"]}

def test_stats_and_runs(http):
    s = http.get(f"{PARSER}/opportunities/stats").json()
    assert s["open_total"] >= 4 and "Tunisia" in s["countries"]
    assert isinstance(http.get(f"{PARSER}/sync/runs").json(), list)

def test_unknown_sync_kind_is_422(http):
    assert http.post(f"{PARSER}/sync/everything").status_code == 422

def test_token_status_does_not_leak_token(http):
    j = http.get(f"{PARSER}/admin/token").json()
    assert set(j) >= {"masked", "auth", "auto_refresh"}
    assert j["masked"] is None or j["masked"].startswith("…")          # наружу только последние 4 символа

@pytest.mark.parametrize("body", [{}, {"token": "short"}, {"token": "a" * 20, "refresh_token": "b" * 20}])
def test_put_token_validation(http, body):
    assert http.put(f"{PARSER}/admin/token", json=body).status_code == 422
