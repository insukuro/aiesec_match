from datetime import date

import pytest

from app.domain.features import NEUTRAL, cost_score, coverage, duration_score, freshness_score
from tests.factories import make_opp, make_profile


def test_coverage_full():
    assert coverage({1: "required", 2: "required"}, {1, 2}) == 1.0

def test_coverage_preferred_weighs_half():
    # закрыт только preferred: 0.5 из (1.0 + 0.5)
    assert coverage({1: "required", 2: "preferred"}, {2}) == pytest.approx(0.5 / 1.5)

def test_coverage_no_requirements_is_neutral():
    assert coverage({}, {1}) == NEUTRAL

def test_duration_inside_range():
    assert duration_score(make_opp(1, duration_weeks=8), make_profile(min_weeks=6, max_weeks=10)) == 1.0

def test_duration_decays_linearly():
    # на 4 недели дольше максимума: 1 - 4/8 = 0.5
    assert duration_score(make_opp(1, duration_weeks=14), make_profile(min_weeks=6, max_weeks=10)) == 0.5

def test_duration_far_is_zero():
    assert duration_score(make_opp(1, duration_weeks=30), make_profile(max_weeks=10)) == 0.0

def test_free_opportunity_cost_is_one():
    assert cost_score(make_opp(1, cost_total=0), make_profile()) == 1.0

def test_freshness_today_is_one():
    assert freshness_score(make_opp(1, date_opened=date.today()), date.today()) == 1.0