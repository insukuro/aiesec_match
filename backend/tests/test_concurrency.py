import asyncio
import uuid
import pytest


@pytest.mark.asyncio
async def test_parallel_put_profile_only_one_version(client):
    r = await client.post("/api/v1/auth/anonymous", json={})
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/me/consents", json={"kind": "pd_processing", "version": "1"}, headers=h)

    body = {"birth_date": "2000-01-01", "english_level": "B2",
            "study": {"status": "bachelor"}, "programmes": ["talent"]}

    async def put():
        return await client.put("/api/v1/profiles/me", json=body, headers=h)

    results = await asyncio.gather(put(), put(), return_exceptions=True)
    statuses = sorted(getattr(r, "status_code", 500) for r in results)
    assert statuses == [200, 200] or statuses == [200, 412]


@pytest.mark.asyncio
async def test_idempotent_recommendation(client, monkeypatch):
    from app.matcher_client import MatcherClient

    async def fake_match(self, payload):
        return {"programme_prior": ["talent"], "groups": []}

    monkeypatch.setattr(MatcherClient, "match", fake_match)

    r = await client.post("/api/v1/auth/anonymous", json={})
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/me/consents", json={"kind": "pd_processing", "version": "1"}, headers=h)
    await client.put("/api/v1/profiles/me", json={
        "birth_date": "2000-01-01", "english_level": "B2",
        "study": {"status": "bachelor"}, "programmes": ["talent"],
    }, headers=h)

    key = str(uuid.uuid4())
    h["Idempotency-Key"] = key
    r1 = await client.post("/api/v1/recommendations", json={"mode": "sync"}, headers=h)
    r2 = await client.post("/api/v1/recommendations", json={"mode": "sync"}, headers=h)
    assert r1.json()["run_id"] == r2.json()["run_id"]