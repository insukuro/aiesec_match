from collections import Counter
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.client import AiesecError
from app.models import Opportunity, SyncRun, utcnow

from .conftest import TODAY, make_row


def opps(factory, **where):
    with factory() as s:
        rows = s.scalars(select(Opportunity)).all()
    return {r.opportunity_id: r for r in rows}


def run(service, kind):
    """Полный жизненный цикл как в реальном сервисе: блокировка -> запись о запуске -> выполнение."""
    run_id = service.try_start(kind)
    assert run_id is not None
    service.execute(run_id, kind)
    with service.Session() as s:
        return s.get(SyncRun, run_id)


# ---------------- full ----------------
def test_full_inserts_only_actual_targets(make_service):
    rows = [
        make_row(1, mc=1559),                                       # Тунис — берём
        make_row(2, mc=1609),                                       # Египет — берём
        make_row(3, mc=1622, lc=941),                               # Адана — берём
        make_row(4, mc=1622, lc=777),                               # другой город Турции — не берём
        make_row(5, mc=1559, slots=0),                              # нет мест
        make_row(6, mc=1559, close=TODAY - timedelta(days=1)),      # дедлайн прошёл
        make_row(7, mc=1559, status="closed"),                      # фейк отфильтрует по status=open
        make_row(8, mc=9999),                                       # чужая страна
    ]
    service, fake, factory = make_service(rows)
    r = run(service, "full")
    assert r.status == "ok", r.error
    assert set(opps(factory)) == {1, 2, 3}
    assert r.stats["inserted"] == 3
    assert r.stats["skipped_no_openings"] == 1
    assert r.stats["skipped_deadline_passed"] == 1
    assert all(o.is_open for o in opps(factory).values())


def test_full_closes_what_disappeared_from_remote(make_service):
    service, fake, factory = make_service([make_row(i) for i in range(1, 6)])
    run(service, "full")
    fake.remote = [r for r in fake.remote if r["id"] != "3"]
    r = run(service, "full")
    assert r.status == "ok"
    o = opps(factory)
    assert o[3].is_open is False and o[3].close_reason == "not_in_open_list" and o[3].closed_at
    assert sum(x.is_open for x in o.values()) == 4


def test_full_is_idempotent(make_service):
    service, fake, factory = make_service([make_row(i) for i in range(1, 4)])
    run(service, "full")
    r = run(service, "full")
    assert r.stats.get("inserted", 0) == 0 and r.stats["updated"] == 3
    assert len(opps(factory)) == 3


def test_safety_guard_refuses_mass_close(make_service):
    """Если выдача внезапно почти пустая — это инцидент, а не 29 закрытых стажировок."""
    service, fake, factory = make_service([make_row(i) for i in range(1, 31)])
    run(service, "full")
    fake.remote = fake.remote[:1]
    r = run(service, "full")
    assert r.status == "failed" and "Предохранитель" in r.error
    assert sum(o.is_open for o in opps(factory).values()) == 30


def test_outage_mid_fetch_closes_nothing(make_service):
    service, fake, factory = make_service([make_row(i) for i in range(1, 7)], page_size=2)
    run(service, "full")
    fake.fail_on_page = 2
    r = run(service, "full")
    assert r.status == "failed" and "simulated outage" in r.error
    assert sum(o.is_open for o in opps(factory).values()) == 6


def test_turkey_cities_by_committee_scope(make_service):
    service, fake, factory = make_service([make_row(1, mc=1622, lc=2452), make_row(2, mc=1622, lc=1)])
    run(service, "full")
    assert set(opps(factory)) == {1}
    modes = [f for m, f in fake.calls if "committee_scope" in f]
    assert modes and modes[0]["committee_scope"] == [941, 2452]


# ---------------- incremental ----------------
def test_incremental_without_bootstrap_falls_back_to_full(make_service):
    service, fake, factory = make_service([make_row(1)])
    r = run(service, "incremental")
    assert r.status == "ok" and r.stats["fallback"].startswith("full")
    assert set(opps(factory)) == {1}


def test_incremental_fetches_only_new_by_date_filter(make_service):
    old = make_row(1, opened=TODAY - timedelta(days=30))
    service, fake, factory = make_service([old])
    run(service, "full")
    fake.calls.clear()
    fake.remote.append(make_row(2, opened=TODAY))
    r = run(service, "incremental")
    assert r.status == "ok", r.error
    assert set(opps(factory)) == {1, 2}
    assert r.stats["inserted"] == 1 and r.stats["fetched"] == 1  # старая стажировка не запрашивалась
    expected_since = (utcnow().date() - timedelta(days=1)).isoformat()
    assert all(f["created"]["from"] == expected_since for _, f in fake.calls)


def test_incremental_never_closes_anything(make_service):
    service, fake, factory = make_service([make_row(1), make_row(2)])
    run(service, "full")
    fake.remote = []  # хоть всё «пропало» — incremental не имеет права закрывать
    run(service, "incremental")
    assert all(o.is_open for o in opps(factory).values())


def test_incremental_falls_back_when_date_filter_unsupported(make_service):
    service, fake, factory = make_service([make_row(1)], supports_range=False)
    run(service, "full")
    r = run(service, "incremental")
    assert r.status == "ok" and "нет фильтра" in r.stats["fallback"]


# ---------------- reconcile ----------------
def seed(make_service, n=5):
    service, fake, factory = make_service([make_row(i) for i in range(1, n + 1)])
    run(service, "full")
    fake.calls.clear()
    return service, fake, factory


def test_reconcile_uses_light_queries_only(make_service):
    service, fake, _ = seed(make_service)
    run(service, "reconcile")
    assert fake.calls and all(m == "slim" for m, _ in fake.calls)


def test_reconcile_updates_closes_and_adds(make_service):
    service, fake, factory = seed(make_service)
    next(r for r in fake.remote if r["id"] == "1")["available_openings"] = 0   # места кончились
    fake.remote = [r for r in fake.remote if r["id"] != "2"]                    # пропала из выдачи
    next(r for r in fake.remote if r["id"] == "3")["available_openings"] = 1   # места поменялись
    fake.remote.append(make_row(6))                                             # incremental её пропустил

    r = run(service, "reconcile")
    assert r.status == "ok", r.error
    o = opps(factory)
    assert o[1].is_open is False and o[1].close_reason == "no_openings"
    assert o[2].is_open is False and o[2].close_reason == "not_in_open_list"
    assert o[3].is_open is True and o[3].available_openings == 1
    assert o[6].is_open is True and o[6].raw is not None   # догружена полная карточка
    assert r.stats["closed"] == 2 and r.stats["new_found"] == 1 and r.stats["gap_fill"] == "by_id"
    assert ("by_id", {"id": 6}) in fake.calls


def test_reconcile_gap_fill_falls_back_to_full_scan(make_service):
    service, fake, factory = seed(make_service)
    fake.single_getter = False
    fake.remote.append(make_row(6))
    r = run(service, "reconcile")
    assert r.stats["gap_fill"] == "full_scan"
    assert 6 in opps(factory)


def test_reconcile_reopens_when_slots_return(make_service):
    service, fake, factory = seed(make_service)
    row1 = next(r for r in fake.remote if r["id"] == "1")
    row1["available_openings"] = 0
    run(service, "reconcile")
    assert opps(factory)[1].is_open is False
    row1["available_openings"] = 2
    r = run(service, "reconcile")
    assert opps(factory)[1].is_open is True and r.stats["reopened"] == 1


def test_reconcile_does_not_clobber_full_fields(make_service):
    service, fake, factory = seed(make_service)
    run(service, "reconcile")
    o = opps(factory)[1]
    assert o.title == "Opportunity 1" and o.home_mc_id == 1559 and o.raw is not None


def test_reconcile_on_empty_db_does_full(make_service):
    service, fake, factory = make_service([make_row(1)])
    r = run(service, "reconcile")
    assert r.stats["fallback"].startswith("full") and set(opps(factory)) == {1}


# ---------------- expire / refresh / lock ----------------
def test_expire_by_deadline_is_local(make_service):
    service, fake, factory = seed(make_service, n=3)
    with factory() as s:
        s.get(Opportunity, 2).applications_close_date = TODAY - timedelta(days=1)
        s.commit()
    assert service.expire_by_deadline() == 1
    o = opps(factory)
    assert o[2].is_open is False and o[2].close_reason == "deadline_passed"
    assert fake.calls == []  # ни одного обращения к AIESEC


def test_refresh_one_updates_single_opportunity(make_service):
    service, fake, factory = seed(make_service, n=3)
    next(r for r in fake.remote if r["id"] == "2")["status"] = "closed"
    assert service.refresh_one(2) == {"result": "closed"}
    assert opps(factory)[2].is_open is False
    assert service.refresh_one(999) == {"result": "not_found_remote"}


def test_only_one_sync_at_a_time(make_service):
    service, _, _ = make_service([make_row(1)])
    run_id = service.try_start("full")
    assert run_id and service.is_running()
    assert service.try_start("incremental") is None
    service.execute(run_id, "full")
    assert not service.is_running()
    assert service.try_start("incremental") is not None


def test_failed_run_is_recorded_and_lock_released(make_service):
    service, fake, _ = make_service([make_row(1), make_row(2), make_row(3)])
    fake.fail_on_page = 1
    r = run(service, "full")
    assert r.status == "failed" and r.finished_at is not None
    assert not service.is_running()