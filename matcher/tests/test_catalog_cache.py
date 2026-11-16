"""Кэш каталога (оптимизация после нагрузочного теста). Время подменяем, чтобы тест не ждал."""
import pytest

from app.repo.catalog_reader import CachedCatalogReader
from tests.factories import BrokenReader, make_opp


class CountingReader:
    def __init__(self):
        self.calls = []

    def list_open(self, kind):
        self.calls.append(kind)
        return [make_opp(len(self.calls), kind)]


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def make(ttl=60):
    inner, clock = CountingReader(), Clock()
    return CachedCatalogReader(inner, ttl, clock=clock), inner, clock


def test_second_call_does_not_touch_db():
    cache, inner, _ = make()
    first = cache.list_open("talent")
    assert cache.list_open("talent") is first
    assert inner.calls == ["talent"]


def test_each_programme_cached_separately():
    cache, inner, _ = make()
    cache.list_open("talent"); cache.list_open("teacher")
    again = cache.list_open("talent")
    assert inner.calls == ["talent", "teacher"]
    assert again[0].programme_kind == "talent"      # из кэша пришли вакансии именно этой программы (дефект D30)


@pytest.mark.parametrize("age, db_calls", [(59.9, 1), (60.0, 2), (60.1, 2)])   # граница срока жизни
def test_ttl_boundary(age, db_calls):
    cache, inner, clock = make(ttl=60)
    cache.list_open("talent")
    clock.t += age
    cache.list_open("talent")
    assert len(inner.calls) == db_calls


def test_error_is_not_cached():
    cache = CachedCatalogReader(BrokenReader(), 60)
    for _ in range(2):
        with pytest.raises(Exception):
            cache.list_open("talent")


def test_cache_is_off_by_default(monkeypatch):
    from app.config import Settings
    monkeypatch.delenv("MATCHER_CATALOG_CACHE_TTL_S", raising=False)
    assert Settings().catalog_cache_ttl_s == 0
