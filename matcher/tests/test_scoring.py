import pytest

from app.domain.scoring import load_weights, rank_programme
from tests.factories import make_opp, make_profile


def rank(opps, p, limit=10, explain=True):
    return rank_programme(opps, p, "talent", {10018}, limit, explain, 0.75, 0.55)


def test_weights_sum_to_one():
    for kind, w in load_weights().items():
        assert sum(w.values()) == pytest.approx(1.0), kind

def test_better_match_ranks_first():
    p = make_profile(background_ids={10253})
    g = rank([make_opp(1, backgrounds={999: "required"}),
              make_opp(2, backgrounds={10253: "required"})], p)
    assert [i.opportunity_id for i in g.items] == [2, 1]

def test_tie_broken_by_id():
    g = rank([make_opp(5), make_opp(3)], make_profile())
    assert [i.opportunity_id for i in g.items] == [3, 5]

def test_family_collapsed():
    g = rank([make_opp(1, family_key="f"), make_opp(2, family_key="f")], make_profile())
    assert len(g.items) == 1
    assert g.items[0].siblings_count == 1

def test_limit_and_total():
    g = rank([make_opp(i) for i in range(1, 6)], make_profile(), limit=2)
    assert len(g.items) == 2
    assert g.total_candidates == 5

def test_no_reasons_without_explain():
    p = make_profile(background_ids={10253})
    g = rank([make_opp(1, backgrounds={10253: "required"})], p, explain=False)
    assert g.items[0].reasons == []