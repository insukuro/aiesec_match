from datetime import date

from app.normalize import normalize

from .conftest import make_row


def test_full_row_maps_to_explicit_columns():
    d = normalize(make_row(123, mc=1559, lc=941))
    assert d["opportunity_id"] == 123  # id -> int, колонка называется opportunity_id
    assert d["home_mc_id"] == 1559 and d["home_lc_id"] == 941
    assert d["programme_name"] == "GTa"
    assert d["host_lc_id"] is None  # host_lc: null -> None, а не пропуск
    assert isinstance(d["applications_close_date"], date)
    assert d["raw"]["id"] == "123"
    assert "id" not in d  # старое неоднозначное имя не протекает в БД


def test_slim_row_does_not_overwrite_missing_columns():
    slim = {"id": "5", "status": "open", "available_openings": 0}
    d = normalize(slim, full=False)
    assert d == {"opportunity_id": 5, "status": "open", "available_openings": 0}


def test_garbage_values_become_none():
    d = normalize({"id": "7", "available_openings": "n/a", "applications_close_date": "not-a-date"})
    assert d["available_openings"] is None
    assert d["applications_close_date"] is None


def test_name_fallbacks_for_programme():
    raw = {"id": "1", "programme": {"id": "9", "short_name": "GTe"}}
    assert normalize(raw)["programme_name"] == "GTe"

def test_remote_updated_at_is_datetime_with_z():
    from datetime import datetime
    d = normalize({"id": "1", "updated_at": "2026-10-15T08:08:11Z"})
    assert d["remote_updated_at"] == datetime(2026, 10, 15, 8, 8, 11)
    assert d["remote_updated_at"].tzinfo is None


def test_remote_updated_at_garbage_becomes_none():
    d = normalize({"id": "1", "updated_at": "not-a-date"})
    assert d["remote_updated_at"] is None