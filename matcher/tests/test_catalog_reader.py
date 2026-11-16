"""Чтение каталога: строка вью catalog.opportunity_v1 + требования -> Opportunity."""
from datetime import date
from pathlib import Path

from app.repo.catalog_reader import FakeCatalogReader, build_opportunity

ROW = {"opportunity_id": "1340614", "programme_kind": "talent", "title": None, "is_open": True,
       "openings": None, "available_openings": 2, "date_opened": "2026-11-01T00:00:00",
       "applications_close_date": date(2026, 12, 31), "duration_weeks": 8, "cost_total": "300.50",
       "cost_currency": "EUR", "lc_id": 2452, "country_code": "TR", "family_key": "Sales#2452"}
REQS = [
    {"kind": "background", "constant_id": 10253, "option": "required"},
    {"kind": "skill", "constant_id": "10161", "option": "preferred"},
    {"kind": "language", "constant_id": 10018, "option": None},          # option пустой = required
    {"kind": "study_level", "constant_id": 10785, "option": None},
    {"kind": "nationality", "constant_id": 10463, "option": "required"},
    {"kind": "skill_development", "constant_id": 1, "option": None},     # не используем, не падаем
]


def test_build_opportunity_maps_row():
    o = build_opportunity(ROW, REQS)
    assert o.opportunity_id == 1340614 and o.title == "" and o.openings == 0
    assert o.date_opened == date(2026, 11, 1) and o.applications_close_date == date(2026, 12, 31)
    assert o.cost_total == 300.5 and o.duration_weeks == 8

def test_build_opportunity_maps_requirements():
    o = build_opportunity(ROW, REQS)
    assert o.backgrounds == {10253: "required"}
    assert o.skills == {10161: "preferred"}
    assert o.languages == {10018: "required"}
    assert o.study_levels == {10785} and o.nationalities == {10463}

def test_fake_catalog_file_is_valid():
    path = Path(__file__).resolve().parent.parent / "app" / "data" / "fake_catalog.json"
    reader = FakeCatalogReader(str(path))
    talent = reader.list_open("talent")
    assert [o.opportunity_id for o in talent] == [1340614]
    assert reader.list_open("teacher") == []

def test_fake_reader_hides_closed_and_full(tmp_path):
    f = tmp_path / "c.json"
    f.write_text('[{"opportunity_id":1,"programme_kind":"talent","is_open":false,"available_openings":3},'
                 '{"opportunity_id":2,"programme_kind":"talent","is_open":true,"available_openings":0},'
                 '{"opportunity_id":3,"programme_kind":"talent","is_open":true,"available_openings":1}]',
                 encoding="utf-8")
    assert [o.opportunity_id for o in FakeCatalogReader(str(f)).list_open("talent")] == [3]
