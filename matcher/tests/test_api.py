from app.deps import get_catalog_reader
from app.main import app
from tests.factories import BrokenReader

BODY = {"profile_id": "t",
        "profile": {"programmes": ["talent"], "english_level": "B2",
                    "spheres": ["marketing", "sales"]},
        "filters": {}}
FEATURES = {"background", "skill", "language", "city", "duration", "cost", "chance", "freshness"}


def test_health(client):
    assert client.get("/health").status_code == 200

def test_dictionary(client):
    r = client.get("/dictionaries/skills")
    assert r.status_code == 200
    assert "id" in r.json()[0] and "name" in r.json()[0]

def test_dictionary_unknown(client):
    assert client.get("/dictionaries/foo").status_code == 422

def test_match_ok(client):
    r = client.post("/v1/match", json=BODY)
    assert r.status_code == 200
    groups = r.json()["groups"]
    assert [g["programme_kind"] for g in groups] == ["talent"]
    first = groups[0]["items"][0]
    assert first["opportunity_id"] == 1               # совпали и образование, и навык
    assert set(first["breakdown"]) == FEATURES
    assert 0 <= first["score"] <= 1

def test_match_ignores_unknown_profile_fields(client):
    body = {**BODY, "profile": {**BODY["profile"], "something_new": 1}}
    assert client.post("/v1/match", json=body).status_code == 200

def test_match_without_programmes_422(client):
    assert client.post("/v1/match", json={"profile": {}}).status_code == 422

def test_unknown_strategy_422(client):
    assert client.post("/v1/match", json={**BODY, "strategy": "magic"}).status_code == 422

def test_catalog_down_503(client):
    app.dependency_overrides[get_catalog_reader] = lambda: BrokenReader()
    assert client.post("/v1/match", json=BODY).status_code == 503