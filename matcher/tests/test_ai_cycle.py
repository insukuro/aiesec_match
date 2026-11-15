"""Кейсы, предложенные ИИ во втором цикле и принятые после сверки с ТЗ (раздел 8 документа).

Номер в имени теста это номер кейса в протоколе цикла (AI-08 ... AI-18).
"""
import random
from datetime import date, timedelta

import pytest

from tests.factories import make_opp

P = {"programmes": ["talent"], "english_level": "B2"}


def test_ai08_request_id_is_echoed(make_client):
    r = make_client([make_opp(1)]).post("/v1/match", json={"request_id": "req-42", "profile_id": "p-1", "profile": P})
    assert r.json()["request_id"] == "req-42" and r.json()["profile_id"] == "p-1"


def test_ai09_took_ms_is_non_negative_int(make_client):
    took = make_client([make_opp(1)]).post("/v1/match", json={"profile": P}).json()["took_ms"]
    assert isinstance(took, int) and took >= 0


def test_ai10_limit_applies_to_each_programme_separately(make_client):
    opps = [make_opp(i, "talent") for i in range(1, 6)] + [make_opp(i, "volunteer") for i in range(11, 16)]
    body = {"profile": {**P, "programmes": ["talent", "volunteer"]}, "limit_per_programme": 2}
    groups = make_client(opps).post("/v1/match", json=body).json()["groups"]
    assert [len(g["items"]) for g in groups] == [2, 2]


def _random_opp(i: int, rnd: random.Random):
    return make_opp(
        i, rnd.choice(["talent", "teacher", "volunteer"]),
        openings=rnd.randint(0, 5), available_openings=rnd.randint(1, 5),
        applicants_count=rnd.randint(0, 300), accepted_count=rnd.randint(0, 5),
        date_opened=date.today() - timedelta(days=rnd.randint(-30, 400)),
        applications_close_date=date.today() + timedelta(days=rnd.randint(0, 90)),
        duration_weeks=rnd.choice([None, 4, 6, 8, 12, 26, 52]),
        cost_total=rnd.choice([None, 0, 150.5, 300, 900]),
        backgrounds={10253: rnd.choice(["required", "preferred"])} if rnd.random() < 0.5 else {},
        skills={10161: rnd.choice(["required", "preferred"])} if rnd.random() < 0.5 else {},
    )


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_ai11_score_always_between_0_and_1_on_random_catalog(make_client, seed):
    rnd = random.Random(seed)
    opps = [_random_opp(i, rnd) for i in range(1, 201)]
    body = {"profile": {**P, "programmes": ["talent", "teacher", "volunteer"], "spheres": ["marketing", "sales"],
                        "duration": {"min_weeks": 6, "max_weeks": 12},
                        "financial": {"willing_to_pay": True, "max_budget_eur": 1000}},
            "limit_per_programme": 50}
    r = make_client(opps).post("/v1/match", json=body)
    assert r.status_code == 200
    items = [it for g in r.json()["groups"] for it in g["items"]]
    assert items and all(0.0 <= it["score"] <= 1.0 for it in items)
    assert all(0.0 <= v <= 1.0 for it in items for v in it["breakdown"].values())


def test_ai13_group_contains_only_its_programme(make_client):
    opps = [make_opp(1, "talent"), make_opp(2, "teacher"), make_opp(3, "volunteer")]
    body = {"profile": {**P, "programmes": ["talent", "teacher", "volunteer"]}}
    groups = make_client(opps).post("/v1/match", json=body).json()["groups"]
    assert {g["programme_kind"]: [it["opportunity_id"] for it in g["items"]] for g in groups} == \
        {"talent": [1], "teacher": [2], "volunteer": [3]}


def test_ai14_very_long_sphere_does_not_crash(make_client):
    r = make_client([make_opp(1)]).post("/v1/match", json={"profile": {**P, "spheres": ["я" * 10_000]}})
    assert r.status_code in (200, 422)                    # ТЗ длину не ограничивает; главное, что не 500


def test_ai15_unicode_profile_id_is_kept(make_client):
    pid = "анкета-№7-🙂"
    r = make_client([make_opp(1)]).post("/v1/match", json={"profile_id": pid, "profile": P})
    assert r.status_code == 200 and r.json()["profile_id"] == pid


def test_ai16_fractional_limit_is_422(make_client):
    r = make_client([make_opp(1)]).post("/v1/match", json={"profile": P, "limit_per_programme": 1.5})
    assert r.status_code == 422


def test_ai17_lowercase_english_level_is_422_with_field_name(make_client):
    """ИИ ожидал 200. По ТЗ уровни пишутся A1...C2, анкета шлёт их так же, поэтому 'b2' это ошибка ввода."""
    r = make_client([make_opp(1)]).post("/v1/match", json={"profile": {**P, "english_level": "b2"}})
    assert r.status_code == 422 and "english_level" in r.text


def test_ai18_no_english_level_means_no_english(make_client):
    """ИИ ожидал 422. По ТЗ поле необязательное: без уровня кандидат просто «не владеет английским»,
    поэтому вакансии с обязательным английским отсеиваются, остальные показываются."""
    opps = [make_opp(1, languages={10018: "required"}), make_opp(2)]
    r = make_client(opps).post("/v1/match", json={"profile": {"programmes": ["talent"]}})
    assert r.status_code == 200
    assert [it["opportunity_id"] for it in r.json()["groups"][0]["items"]] == [2]
