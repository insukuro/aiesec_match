import uuid
import pytest


def _signal_url(sig): return f"/api/v1/feedback?signal={sig}"


@pytest.mark.asyncio
async def test_post_feedback_204(client, auth_headers, catalog_opps):
    open_id, _ = catalog_opps
    r = await client.post(
        "/api/v1/feedback",
        json={"opportunity_id": open_id, "signal": "liked"},
        headers=auth_headers,
    )
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_post_feedback_idempotent(client, auth_headers, catalog_opps):
    open_id, _ = catalog_opps
    body = {"opportunity_id": open_id, "signal": "liked"}
    r1 = await client.post("/api/v1/feedback", json=body, headers=auth_headers)
    r2 = await client.post("/api/v1/feedback", json=body, headers=auth_headers)
    assert r1.status_code == r2.status_code == 204
    liked = await client.get("/api/v1/feedback/liked", headers=auth_headers)
    total = liked.json()["total"]
    # ровно одна запись, несмотря на два POST
    assert total == 1


@pytest.mark.asyncio
async def test_post_feedback_invalid_signal(client, auth_headers, catalog_opps):
    open_id, _ = catalog_opps
    r = await client.post(
        "/api/v1/feedback",
        json={"opportunity_id": open_id, "signal": "bogus"},
        headers=auth_headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_delete_feedback(client, auth_headers, catalog_opps):
    open_id, _ = catalog_opps
    await client.post(
        "/api/v1/feedback",
        json={"opportunity_id": open_id, "signal": "liked"},
        headers=auth_headers,
    )
    r = await client.delete(f"/api/v1/feedback/{open_id}?signal=liked", headers=auth_headers)
    assert r.status_code == 204
    liked = await client.get("/api/v1/feedback/liked", headers=auth_headers)
    assert all(i["opportunity_id"] != open_id for i in liked.json()["items"])


@pytest.mark.asyncio
async def test_liked_lists_only_liked(client, auth_headers, catalog_opps):
    open_id, closed_id = catalog_opps
    await client.post(
        "/api/v1/feedback",
        json={"opportunity_id": open_id, "signal": "liked"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/feedback",
        json={"opportunity_id": closed_id, "signal": "hidden"},
        headers=auth_headers,
    )
    r = await client.get("/api/v1/feedback/liked", headers=auth_headers)
    ids = [i["opportunity_id"] for i in r.json()["items"]]
    assert ids == [open_id]


@pytest.mark.asyncio
async def test_hidden_includes_disliked(client, auth_headers, catalog_opps):
    open_id, closed_id = catalog_opps
    await client.post(
        "/api/v1/feedback",
        json={"opportunity_id": open_id, "signal": "disliked"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/feedback",
        json={"opportunity_id": closed_id, "signal": "hidden"},
        headers=auth_headers,
    )
    r = await client.get("/api/v1/feedback/hidden", headers=auth_headers)
    ids = {i["opportunity_id"] for i in r.json()["items"]}
    assert ids == {open_id, closed_id}
    assert r.json()["total"] == 2


@pytest.mark.asyncio
async def test_feedback_pagination(client, auth_headers, catalog_opps):
    open_id, closed_id = catalog_opps
    for oid in (open_id, closed_id):
        await client.post(
            "/api/v1/feedback",
            json={"opportunity_id": oid, "signal": "liked"},
            headers=auth_headers,
        )
    r = await client.get("/api/v1/feedback/liked?limit=1&offset=0", headers=auth_headers)
    assert len(r.json()["items"]) == 1
    assert r.json()["total"] == 2