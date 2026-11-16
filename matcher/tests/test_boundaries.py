"""Граничные значения (Коцур: значение на границе, на шаг ниже и на шаг выше).

Каждая таблица ниже — это одна граница из ТЗ-M и три точки вокруг неё.
"""
import math
from datetime import date, timedelta

import pytest

from app.domain.features import (NEUTRAL, chance_scores, city_score, cost_score, coverage,
                                 duration_score, freshness_score, language_score)
from app.domain.filters import hard_filter
from app.domain.scoring import label, make_reasons, load_weights, rank_programme
from app.schemas import MatchFilters
from tests.factories import make_opp, make_profile

TODAY = date.today()
EN = 10018


def kept(opps, p, min_english="B1", **filters):
    return [o.opportunity_id for o in hard_filter(opps, p, MatchFilters(**filters), min_english)]


# ---------- жёсткие фильтры (ТЗ-M 2.3) ----------
@pytest.mark.parametrize("min_english, level, passes", [
    ("B1", "A2", False), ("B1", "B1", True), ("B1", "B2", True),      # talent
    ("B2", "B1", False), ("B2", "B2", True), ("B2", "C1", True),      # teacher
    ("A2", "A1", False), ("A2", "A2", True), ("A2", "B1", True),      # volunteer
])
def test_english_threshold(min_english, level, passes):
    o = make_opp(1, languages={EN: "required"})
    assert (kept([o], make_profile(english_level=level), min_english) == [1]) is passes

def test_english_not_set_fails_required_english():
    assert kept([make_opp(1, languages={EN: "required"})], make_profile(english_level=None)) == []

@pytest.mark.parametrize("delta_days, passes", [(-1, False), (0, True), (1, True)])
def test_deadline_boundary(delta_days, passes):
    o = make_opp(1, applications_close_date=TODAY + timedelta(days=delta_days))
    assert (kept([o], make_profile()) == [1]) is passes

def test_no_deadline_passes():
    assert kept([make_opp(1, applications_close_date=None)], make_profile()) == [1]

@pytest.mark.parametrize("places, passes", [(-1, False), (0, False), (1, True)])
def test_available_openings_boundary(places, passes):
    assert (kept([make_opp(1, available_openings=places)], make_profile()) == [1]) is passes

@pytest.mark.parametrize("budget, passes", [(299.99, False), (300, True), (300.01, True)])
def test_budget_boundary(budget, passes):
    o = make_opp(1, cost_total=300.0, cost_currency="EUR")
    assert (kept([o], make_profile(max_budget_eur=budget)) == [1]) is passes

def test_free_opportunity_passes_even_if_not_willing_to_pay():
    assert kept([make_opp(1, cost_total=0)], make_profile(willing_to_pay=False)) == [1]

def test_non_eur_cost_is_not_compared_with_budget():
    # валюту не умеем пересчитывать, поэтому не режем (известное ограничение MVP)
    o = make_opp(1, cost_total=99999.0, cost_currency="INR")
    assert kept([o], make_profile(max_budget_eur=100)) == [1]

def test_required_language_must_all_be_covered():
    o = make_opp(1, languages={EN: "required", 10043: "required"})
    assert kept([o], make_profile(english_level="C1")) == []
    assert kept([o], make_profile(english_level="C1", language_ids={10043})) == [1]

def test_preferred_language_does_not_filter():
    assert kept([make_opp(1, languages={10043: "preferred"})], make_profile()) == [1]

def test_study_level_filter():
    o = make_opp(1, study_levels={10785})
    assert kept([o], make_profile(study_level_ids={10782})) == []
    assert kept([o], make_profile(study_level_ids={10785})) == [1]
    assert kept([o], make_profile(study_level_ids=set())) == [1]       # не указал, не режем

def test_country_filter():
    opps = [make_opp(1, country_code="TR"), make_opp(2, country_code="PL"), make_opp(3, country_code=None)]
    assert kept(opps, make_profile(), country_codes=["TR"]) == [1]
    assert kept(opps, make_profile()) == [1, 2, 3]


# ---------- признаки (ТЗ-M 2.4) ----------
@pytest.mark.parametrize("weeks, expected", [
    (6, 1.0), (10, 1.0),                 # обе границы диапазона входят
    (5, 0.875), (11, 0.875),             # шаг наружу: 1 - 1/8
    (17, 0.125), (18, 0.0), (19, 0.0),   # 7, 8 и 9 недель от границы
])
def test_duration_boundaries(weeks, expected):
    p = make_profile(min_weeks=6, max_weeks=10)
    assert duration_score(make_opp(1, duration_weeks=weeks), p) == pytest.approx(expected)

def test_duration_unknown_is_neutral():
    assert duration_score(make_opp(1, duration_weeks=None), make_profile(min_weeks=6)) == NEUTRAL
    assert duration_score(make_opp(1, duration_weeks=8), make_profile()) == NEUTRAL

@pytest.mark.parametrize("cost, budget, expected", [
    (300.0, 300, 1.0), (300.0, 299, 0.0), (300.0, None, NEUTRAL), (None, 300, NEUTRAL), (0, None, 1.0),
])
def test_cost_score(cost, budget, expected):
    assert cost_score(make_opp(1, cost_total=cost), make_profile(max_budget_eur=budget)) == expected

@pytest.mark.parametrize("days_ago, expected", [(0, 1.0), (90, math.exp(-1)), (180, math.exp(-2))])
def test_freshness_decay(days_ago, expected):
    o = make_opp(1, date_opened=TODAY - timedelta(days=days_ago))
    assert freshness_score(o, TODAY) == pytest.approx(expected)

def test_freshness_unknown_is_neutral():
    assert freshness_score(make_opp(1, date_opened=None), TODAY) == NEUTRAL

@pytest.mark.parametrize("have, expected", [(set(), 0.0), ({1}, 0.5), ({1, 2}, 1.0)])
def test_coverage_boundaries(have, expected):
    assert coverage({1: "required", 2: "required"}, have) == expected

def test_language_score_counts_only_preferred():
    o = make_opp(1, languages={EN: "required", 10043: "preferred", 10048: "preferred"})
    assert language_score(o, {EN}) == 0.0
    assert language_score(o, {EN, 10043}) == 0.5
    assert language_score(make_opp(2, languages={EN: "required"}), {EN}) == NEUTRAL

def test_city_score():
    o = make_opp(1, lc_id=941)
    assert city_score(o, make_profile()) == NEUTRAL
    assert city_score(o, make_profile(preferred_lc_ids={941})) == 1.0
    assert city_score(o, make_profile(preferred_lc_ids={5})) == 0.0

def test_chance_single_or_equal_is_neutral():
    assert chance_scores([make_opp(1)]) == {1: NEUTRAL}
    assert chance_scores([make_opp(1), make_opp(2)]) == {1: NEUTRAL, 2: NEUTRAL}
    assert chance_scores([]) == {}

def test_chance_percentile_extremes():
    easy = make_opp(1, openings=5, available_openings=5, applicants_count=10, accepted_count=8)
    hard = make_opp(2, openings=5, available_openings=1, applicants_count=200, accepted_count=1)
    ch = chance_scores([easy, hard])
    assert ch == {1: 1.0, 2: 0.0}


# ---------- итог (ТЗ-M 2.5) ----------
@pytest.mark.parametrize("score, expected", [
    (0.75, "excellent"), (0.7499, "good"), (0.55, "good"), (0.5499, "fair"), (0.0, "fair"), (1.0, "excellent"),
])
def test_label_thresholds(score, expected):
    assert label(score, 0.75, 0.55) == expected

@pytest.mark.parametrize("value, has_reason", [(0.69, False), (0.7, True), (1.0, True)])
def test_positive_reason_threshold(value, has_reason):
    f = dict.fromkeys(load_weights()["talent"], 0.0)
    f["chance"] = 0.5
    f["background"] = value
    codes = [r.code for r in make_reasons(f, load_weights()["talent"])]
    assert ("background_match" in codes) is has_reason

@pytest.mark.parametrize("chance, negative", [(0.29, True), (0.3, False)])
def test_negative_reason_threshold(chance, negative):
    f = dict.fromkeys(load_weights()["talent"], 0.0)
    f["chance"] = chance
    codes = [r.code for r in make_reasons(f, load_weights()["talent"])]
    assert ("chance_low" in codes) is negative

def test_at_most_three_positive_reasons():
    f = dict.fromkeys(load_weights()["talent"], 1.0)
    reasons = make_reasons(f, load_weights()["talent"])
    assert len([r for r in reasons if r.polarity == "positive"]) == 3

@pytest.mark.parametrize("kind", ["talent", "teacher", "volunteer"])
def test_score_stays_in_unit_interval(kind):
    best = make_opp(1, kind=kind, backgrounds={1: "required"}, skills={2: "required"},
                    languages={3: "preferred"}, lc_id=7, duration_weeks=8, cost_total=0, date_opened=TODAY)
    worst = make_opp(2, kind=kind, backgrounds={9: "required"}, skills={9: "required"},
                     languages={9: "preferred"}, lc_id=8, duration_weeks=60, cost_total=900.0,
                     date_opened=TODAY - timedelta(days=3000), applicants_count=500)
    p = make_profile(background_ids={1}, skill_ids={2}, language_ids={3}, preferred_lc_ids={7},
                     min_weeks=6, max_weeks=10, max_budget_eur=100)
    g = rank_programme([best, worst], p, kind, {3}, 10, True, 0.75, 0.55)
    assert [i.opportunity_id for i in g.items] == [1, 2]
    assert all(0.0 <= i.score <= 1.0 for i in g.items)
    assert all(0.0 <= v <= 1.0 for i in g.items for v in i.breakdown.values())


# ---------- API: границы параметров запроса ----------
@pytest.mark.parametrize("limit, status", [(0, 422), (1, 200), (50, 200), (51, 422)])
def test_limit_per_programme_boundary(make_client, limit, status):
    c = make_client([make_opp(i) for i in range(1, 61)])
    r = c.post("/v1/match", json={"profile": {"programmes": ["talent"]}, "limit_per_programme": limit})
    assert r.status_code == status
    if status == 200:
        assert len(r.json()["groups"][0]["items"]) == limit
        assert r.json()["groups"][0]["total_candidates"] == 60

def test_default_limit_is_ten(make_client):
    c = make_client([make_opp(i) for i in range(1, 31)])
    r = c.post("/v1/match", json={"profile": {"programmes": ["talent"]}})
    assert len(r.json()["groups"][0]["items"]) == 10
