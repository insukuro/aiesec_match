"""Матчер поверх настоящей базы (MATCHER_CATALOG_SOURCE=db): чтение вью catalog и расчёт на реальных строках."""
import pytest

from conftest import MATCHER

pytestmark = [pytest.mark.critical, pytest.mark.bug]

BODY = {"profile": {"programmes": ["talent"], "english_level": "B2", "other_languages": ["ru"],
                    "spheres": ["marketing", "sales"], "nationality": "RU",
                    "study": {"status": "bachelor"}, "duration": {"min_weeks": 6, "max_weeks": 12}},
        "limit_per_programme": 50}


def items(http, body=BODY):
    r = http.post(f"{MATCHER}/v1/match", json=body)
    assert r.status_code == 200, r.text
    return {i["opportunity_id"]: i for g in r.json()["groups"] for i in g["items"]}


def test_matcher_reads_requirements_from_views(http, catalog):
    """Красный, пока не исправлен BUG-DB-01 или пока матчер смотрит в файл-заглушку."""
    found = items(http)
    assert catalog["ideal"] in found
    top = found[catalog["ideal"]]
    assert top["breakdown"]["background"] == pytest.approx(0.5)        # знает Marketing, не знает Business administration
    assert top["breakdown"]["skill"] == 1.0
    assert top["breakdown"]["duration"] == 1.0
    assert top["family_key"] == "QA Sales at Cooler Systems#2452"

def test_matcher_skips_closed_full_and_expired(http, catalog):
    found = items(http)
    assert found, "подбор пуст"
    assert not {catalog["closed"], catalog["full"], catalog["expired"]} & set(found)

def test_required_russian_filters_out_candidate_without_it(http, catalog):
    body = {**BODY, "profile": {**BODY["profile"], "other_languages": []}}
    found = items(http, body)
    assert catalog["weak"] in found and catalog["ideal"] not in found

def test_country_filter_through_matcher(http, catalog):
    body = {"profile": {"programmes": ["volunteer"], "english_level": "B2"},
            "filters": {"country_codes": ["TN"]}, "limit_per_programme": 50}
    assert catalog["volunteer"] in items(http, body)
