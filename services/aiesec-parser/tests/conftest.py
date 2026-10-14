"""Общие фикстуры. Сеть не используется: AIESEC подменён FakeClient."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from datetime import date, timedelta
from types import SimpleNamespace

# Settings() создаётся при импорте app.main — окружение нужно выставить до любого импорта приложения.
_TMP = tempfile.mkdtemp(prefix="parser-tests-")
os.environ.setdefault("AIESEC_TOKEN", "test-token")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/api.db"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["API_KEY"] = ""
os.environ["TARGETS_FILE"] = str(Path(__file__).resolve().parent.parent / "targets.json")

import pytest  # noqa: E402

from app.client import AiesecError  # noqa: E402
from app.config import Settings, Targets  # noqa: E402
from app.models import make_session_factory  # noqa: E402
from app.sync import SyncService  # noqa: E402

TODAY = date.today()
FILTERS = {"home_mcs", "committee_scope", "programmes", "status", "created"}


def make_row(oid, mc=1559, lc=None, status="open", slots=3, close=None, opened=None, title=None):
    """Строка в том виде, как её отдаёт GraphQL: id строкой, вложенные объекты, даты ISO."""
    close = close or TODAY + timedelta(days=30)
    opened = opened or TODAY - timedelta(days=10)
    return {
        "id": str(oid),
        "title": title or f"Opportunity {oid}",
        "status": status,
        "current_status": status,
        "location": "Somewhere",
        "openings": slots,
        "available_openings": slots,
        "applicants_count": 0,
        "accepted_count": 0,
        "date_opened": opened.isoformat(),
        "applications_close_date": close.isoformat(),
        "programme": {"id": "8", "short_name_display": "GTa"},
        "home_mc": {"id": str(mc), "name": "Country"},
        "home_lc": {"id": str(lc or 1), "name": "LC"},
        "host_lc": None,
    }


class FakeClient:
    """Имитирует AiesecClient: фильтрует выдачу по гео/статусу/created.from, пагинирует, пишет вызовы."""

    def __init__(self, rows=None, supports_range=True, page_size=2, fail_on_page=None, single_getter=True):
        self.remote: list[dict] = list(rows or [])
        self.supports_range = supports_range
        self.page_size = page_size
        self.fail_on_page = fail_on_page  # номер страницы, на которой «падаем»
        self.single_getter = single_getter
        self.calls: list[tuple[str, dict]] = []
        self.broken_fields: set[str] = set()
        self.auth_ok: bool | None = True

    def schema(self):
        return SimpleNamespace(field="searchOpportunities", item_type="Opportunity",
                               filters={k: {} for k in FILTERS})

    def supports_range_filter(self, name):
        return self.supports_range and name in FILTERS

    @staticmethod
    def _slim(r):
        keys = ("id", "status", "current_status", "available_openings", "applicants_count",
                "accepted_count", "applications_close_date")
        return {k: r[k] for k in keys if k in r}

    def _match(self, r, f):
        if f.get("status") and r["status"] != f["status"]:
            return False
        if "home_mcs" in f and int(r["home_mc"]["id"]) not in f["home_mcs"]:
            return False
        if "committee_scope" in f:
            ids = {int(r["home_lc"]["id"])} | ({int(r["host_lc"]["id"])} if r.get("host_lc") else set())
            if not ids & set(f["committee_scope"]):
                return False
        since = (f.get("created") or {}).get("from")
        if since and r["date_opened"] < since:
            return False
        return True

    def iter_pages(self, filters, mode="full"):
        self.calls.append((mode, filters))
        rows = [r for r in self.remote if self._match(r, filters)]
        for n, i in enumerate(range(0, len(rows), self.page_size), start=1):
            if self.fail_on_page == n:
                raise AiesecError("simulated outage")
            chunk = rows[i:i + self.page_size]
            yield [self._slim(r) for r in chunk] if mode == "slim" else chunk

    def get_opportunity(self, oid):
        self.calls.append(("by_id", {"id": oid}))
        if not self.single_getter:
            from app.client import NotSupported
            raise NotSupported("no opportunity(id)")
        return next((r for r in self.remote if int(r["id"]) == int(oid)), None)

    def search_offices(self, q, limit=50):
        return [{"id": "1559", "name": "Tunisia", "tag": "MC"}]


def make_targets():
    return Targets(
        countries={"Tunisia": 1559, "Egypt": 1609},
        turkey_mc_id=1622,
        turkey_cities={"Adana": 941, "Konya": 2452},
        base_filters={"programmes": [8, 9], "status": "open"},
        only_with_openings=True,
    )


@pytest.fixture
def make_service(tmp_path):
    def _make(rows=None, **fake_kw):
        fake = FakeClient(rows, **fake_kw)
        settings = Settings(aiesec_token="x", database_url="sqlite://", api_key=None)
        factory = make_session_factory(f"sqlite:///{tmp_path}/unit.db")
        return SyncService(fake, settings, make_targets(), factory), fake, factory
    return _make