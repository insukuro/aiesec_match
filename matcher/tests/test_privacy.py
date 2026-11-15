"""152-ФЗ и ТЗ: в логи попадают только идентификаторы, без данных анкеты."""
import logging

from tests.factories import make_opp

SECRET_PROFILE = {"programmes": ["talent"], "english_level": "C1", "nationality": "RU",
                  "spheres": ["marketing"], "motivation_text": "ОЧЕНЬ ЛИЧНЫЙ ТЕКСТ",
                  "financial": {"max_budget_eur": 12345}}


def test_log_has_only_ids(make_client, caplog):
    c = make_client([make_opp(1)])
    with caplog.at_level(logging.INFO, logger="matcher"):
        r = c.post("/v1/match", json={"profile_id": "hash-abc", "profile": SECRET_PROFILE})
    assert r.status_code == 200
    text = caplog.text
    assert "hash-abc" in text                                   # id для трассировки есть
    for private in ("ОЧЕНЬ ЛИЧНЫЙ ТЕКСТ", "12345", "marketing", "C1", "RU"):
        assert private not in text

def test_response_does_not_echo_profile(make_client):
    c = make_client([make_opp(1)])
    r = c.post("/v1/match", json={"profile_id": "hash-abc", "profile": SECRET_PROFILE})
    assert "ОЧЕНЬ ЛИЧНЫЙ ТЕКСТ" not in r.text and "12345" not in r.text
