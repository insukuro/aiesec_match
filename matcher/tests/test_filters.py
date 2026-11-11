from datetime import date, timedelta

from app.domain.filters import hard_filter
from app.schemas import MatchFilters
from tests.factories import make_opp, make_profile


def run(opps, p, **filters):
    return [o.opportunity_id for o in hard_filter(opps, p, MatchFilters(**filters), "B1")]


def test_english_threshold():
    o = make_opp(1, languages={10018: "required"})
    assert run([o], make_profile(english_level="A2")) == []
    assert run([o], make_profile(english_level="B1")) == [1]

def test_closed_or_no_places_excluded():
    assert run([make_opp(1, is_open=False), make_opp(2, available_openings=0)], make_profile()) == []

def test_deadline_passed_excluded():
    o = make_opp(1, applications_close_date=date.today() - timedelta(days=1))
    assert run([o], make_profile()) == []

def test_nationality():
    o = make_opp(1, nationalities={10463})
    assert run([o], make_profile(nationality_id=10353)) == []
    assert run([o], make_profile(nationality_id=10463)) == [1]
    assert run([o], make_profile(nationality_id=None)) == [1]      # не указал, не режем

def test_budget():
    o = make_opp(1, cost_total=300.0)
    assert run([o], make_profile(willing_to_pay=False)) == []
    assert run([o], make_profile(max_budget_eur=200)) == []
    assert run([o], make_profile(max_budget_eur=500)) == [1]

def test_exclude_ids():
    assert run([make_opp(1)], make_profile(), exclude_opportunity_ids=[1]) == []