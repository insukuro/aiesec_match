import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _register(client):
    email = f"u{uuid.uuid4().hex[:8]}@example.com"
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd!"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/api/v1/me/consents",
        json={"kind": "pd_processing", "version": "1"},
        headers=h,
    )
    return h

@pytest.mark.asyncio
async def test_parallel_put_profile_only_one_version():
    body = {
        "birth_date": "2000-01-01",
        "english_level": "B2",
        "study": {"status": "bachelor"},
        "programmes": ["talent"],
    }
    # отдельный клиент на каждый запрос — BaseHTTPMiddleware ломается
    # при параллельных запросах через один ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        h = await _register(c)

    async def put():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.put("/api/v1/profiles/me", json=body, headers=h)

    results = await asyncio.gather(put(), put(), return_exceptions=True)
    for r in results:
        assert not isinstance(r, Exception), r
    statuses = sorted(r.status_code for r in results)
    assert statuses in ([200, 200], [200, 412]), statuses


@pytest.mark.asyncio
async def test_idempotent_recommendation(client, monkeypatch):
    from app.matcher_client import MatcherClient

    async def fake_match(self, payload):
        return {"programme_prior": ["talent"], "groups": []}

    monkeypatch.setattr(MatcherClient, "match", fake_match)

    h = await _register(client)

    rp = await client.put(
        "/api/v1/profiles/me",
        json={
            "birth_date": "2000-01-01",
            "english_level": "B2",
            "study": {"status": "bachelor"},
            "programmes": ["talent"],
        },
        headers=h,
    )
    assert rp.status_code == 200, rp.text

    h["Idempotency-Key"] = str(uuid.uuid4())
    r1 = await client.post("/api/v1/recommendations", json={"mode": "sync"}, headers=h)
    assert r1.status_code == 200, r1.text
    r2 = await client.post("/api/v1/recommendations", json={"mode": "sync"}, headers=h)
    assert r2.status_code == 200, r2.text
    assert r1.json()["run_id"] == r2.json()["run_id"]