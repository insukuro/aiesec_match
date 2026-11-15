"""Выбор программ (ТЗ-M 2.1, 2.2): фильтр запроса -> программы анкеты -> роутер v0."""
import pytest

from app.routers.match import route_programmes
from app.schemas import MatchRequest


def prior(profile, filters=None):
    return route_programmes(MatchRequest(profile=profile, filters=filters or {}))


def test_filter_overrides_profile_programmes():
    assert prior({"programmes": ["talent"]}, {"programme_kinds": ["volunteer"]}) == {"volunteer": 1.0}

def test_profile_programmes_used_when_no_filter():
    assert prior({"programmes": ["teacher", "talent"]}) == {"teacher": 1.0, "talent": 1.0}

def test_duplicates_removed_order_kept():
    assert list(prior({"programmes": ["talent", "teacher", "talent"]})) == ["talent", "teacher"]

@pytest.mark.parametrize("profile, expected", [
    ({"spheres": ["teaching_kids"]}, ["teacher"]),
    ({"spheres": ["marketing"]}, ["talent"]),
    ({"activities": ["ecology"]}, ["volunteer"]),
    ({"spheres": ["teaching_kids", "it"], "activities": ["events"]}, ["teacher", "talent", "volunteer"]),
])
def test_router_v0_by_spheres_and_activities(profile, expected):
    assert list(prior(profile)) == expected

def test_router_v0_priors_split_evenly():
    p = prior({"spheres": ["teaching_kids", "it"], "activities": ["events"]})
    assert sum(p.values()) == pytest.approx(1.0, abs=0.01)
    assert all(v >= 0.2 for v in p.values())                 # ТЗ: приор не ниже 0.2

def test_nothing_to_route_gives_empty():
    assert prior({}) == {}

def test_groups_follow_prior_order(make_client):
    from tests.factories import make_opp
    c = make_client([make_opp(1), make_opp(2, kind="volunteer")])
    r = c.post("/v1/match", json={"profile": {"programmes": ["volunteer", "talent"], "english_level": "B2"}})
    assert [g["programme_kind"] for g in r.json()["groups"]] == ["volunteer", "talent"]
