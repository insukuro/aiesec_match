"""Тесты против настоящего AIESEC. Запуск: AIESEC_TOKEN=... pytest -m live. Только чтение, 3-4 запроса."""
import os

import pytest

from app.client import AiesecClient

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def live():
    token = os.environ.get("AIESEC_TOKEN")
    if not token or token == "test-token":
        pytest.skip("нужен настоящий AIESEC_TOKEN")
    return AiesecClient(token, "https://gis-api.aiesec.org/graphql", per_page=5, delay=1.0)


def test_schema_has_filters_we_depend_on(live):
    f = live.schema().filters
    for name in ("home_mcs", "committee_scope", "programmes", "status"):
        assert name in f, f"AIESEC убрал фильтр {name}"


def test_incremental_date_filter_is_usable(live):
    assert live.supports_range_filter("created"), "нет фильтра created {from,to} — incremental уйдёт в full"


def test_single_opportunity_getter_exists(live):
    assert "opportunity" in live.query_fields()


def test_one_page_for_tunisia_has_expected_shape(live):
    rows = live.search_page({"home_mcs": [1559], "programmes": [8, 9], "status": "open"}, 1)
    assert isinstance(rows, list)
    if rows:
        from app.normalize import normalize
        d = normalize(rows[0])
        assert d["opportunity_id"] and d["home_mc_id"] == 1559