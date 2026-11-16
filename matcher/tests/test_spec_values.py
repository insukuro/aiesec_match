"""Числа из ТЗ-M, зашитые в настройки: веса, пороги, минимальный английский.

Если кто-то случайно поменяет вес или порог, обычные тесты могут остаться зелёными
(порядок вакансий в простых примерах не изменится). Этот файл ловит именно такие правки.
"""
import pytest

from app.config import Settings
from app.domain.features import chance_scores
from app.domain.scoring import load_weights
from tests.factories import make_opp

EN = 10018
SPEC_WEIGHTS = {   # ТЗ-M 2.4, таблица весов
    "talent":    {"background": 0.35, "skill": 0.15, "language": 0.15, "city": 0.0,  "duration": 0.05, "cost": 0.10, "chance": 0.15, "freshness": 0.05},
    "teacher":   {"background": 0.25, "skill": 0.0,  "language": 0.25, "city": 0.0,  "duration": 0.10, "cost": 0.10, "chance": 0.20, "freshness": 0.10},
    "volunteer": {"background": 0.25, "skill": 0.0,  "language": 0.05, "city": 0.20, "duration": 0.20, "cost": 0.10, "chance": 0.15, "freshness": 0.05},
}


@pytest.mark.parametrize("kind", ["talent", "teacher", "volunteer"])
def test_weights_match_spec(kind):
    assert load_weights()[kind] == SPEC_WEIGHTS[kind]

def test_default_thresholds_match_spec():
    s = Settings()
    assert (s.label_excellent, s.label_good) == (0.75, 0.55)
    assert s.min_english == {"talent": "B1", "teacher": "B2", "volunteer": "A2"}

@pytest.mark.parametrize("kind, level, found", [
    ("talent", "A2", False), ("talent", "B1", True),
    ("teacher", "B1", False), ("teacher", "B2", True),
    ("volunteer", "A1", False), ("volunteer", "A2", True),
])
def test_min_english_per_programme_through_api(make_client, kind, level, found):
    c = make_client([make_opp(1, kind=kind, languages={EN: "required"})])
    r = c.post("/v1/match", json={"profile": {"programmes": [kind], "english_level": level}})
    assert (len(r.json()["groups"][0]["items"]) == 1) is found

def test_chance_smoothing_one_lucky_applicant_does_not_win():
    # A: приняли 1 из 1. B: приняли 40 из 50. C: 0 из 100 (тянет среднюю вниз).
    a = make_opp(1, openings=1, available_openings=1, applicants_count=1, accepted_count=1)
    b = make_opp(2, openings=1, available_openings=1, applicants_count=50, accepted_count=40)
    c = make_opp(3, openings=1, available_openings=1, applicants_count=100, accepted_count=0)
    ch = chance_scores([a, b, c])
    assert ch[2] > ch[1] > ch[3]                 # сглаживание a=10 не даёт «1 из 1» обогнать «40 из 50»

def test_score_is_weighted_sum_of_breakdown(make_client):
    c = make_client([make_opp(1, backgrounds={10253: "required"}, skills={10161: "required"},
                              languages={EN: "required"}, duration_weeks=8, cost_total=0)])
    body = {"profile": {"programmes": ["talent"], "english_level": "B2", "spheres": ["marketing"],
                        "duration": {"min_weeks": 6, "max_weeks": 10}}}
    item = c.post("/v1/match", json=body).json()["groups"][0]["items"][0]
    expected = sum(SPEC_WEIGHTS["talent"][k] * v for k, v in item["breakdown"].items())
    assert item["score"] == pytest.approx(expected, abs=1e-3)
