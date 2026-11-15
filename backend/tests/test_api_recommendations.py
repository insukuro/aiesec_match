import uuid
import pytest
from app.errors import MatcherTimeout


def _idem():
    return str(uuid.uuid4())  # >= 8 символов


def _profile_body(**over):
    base = {
        "birth_date": "2000-01-01",
        "english_level": "B2",
        "study": {"status": "bachelor"},
        "programmes": ["talent"],
        "spheres": ["it"],
        "desired_countries": ["TR"],
        "duration": {"min_weeks": 6},
        "start_window": "asap",
        "motivation_text": "хочу",
    }
    base.update(over)
    return base


async def _setup_profile(client, headers):
    """consent + profile через API, как в реальном флоу."""
    r = await client.post(
        "/api/v1/me/consents",
        json={"kind": "pd_processing", "version": "1"},
        headers=headers,
    )
    assert r.status_code == 204, r.text
    r = await client.put("/api/v1/profiles/me", json=_profile_body(), headers=headers)
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_run_without_profile(client, auth_headers):
    r = await client.post(
        "/api/v1/recommendations",
        json={"mode": "sync"},
        headers={**auth_headers, "Idempotency-Key": _idem()},
    )
    assert r.status_code == 404
    assert r.json()["type"] == "/problems/profile-not-found"


@pytest.mark.asyncio
async def test_run_incomplete_profile(client, auth_headers):
    # consent без профиля — profile есть, но пустой (PUT не делали)
    r = await client.post(
        "/api/v1/me/consents",
        json={"kind": "pd_processing", "version": "1"}, headers=auth_headers,
    )
    assert r.status_code == 204
    # создаём минимальный профиль (только programmes) → missing_for_match вернёт english_level и т.д.
    r = await client.put(
        "/api/v1/profiles/me",
        json={"programmes": ["talent"], "birth_date": "2000-01-01"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text

    r = await client.post(
        "/api/v1/recommendations",
        json={"mode": "sync"},
        headers={**auth_headers, "Idempotency-Key": _idem()},
    )
    assert r.status_code == 409
    body = r.json()
    assert body["type"] == "/problems/profile-incomplete"
    locs = [e["loc"][-1] for e in body["errors"]]
    assert "english_level" in locs


@pytest.mark.asyncio
async def test_run_success_with_matcher(client, auth_headers, fake_matcher, catalog_opps):
    open_id, closed_id = catalog_opps
    fake_matcher.response = {
        "programme_prior": ["talent"],
        "groups": [{
            "programme_kind": "talent",
            "total_candidates": 2,
            "items": [
                {"opportunity_id": open_id, "score": 0.9, "breakdown": {}, "reasons": []},
                {"opportunity_id": closed_id, "score": 0.7, "breakdown": {}, "reasons": []},
            ],
        }],
    }
    await _setup_profile(client, auth_headers)

    r = await client.post(
        "/api/v1/recommendations",
        json={"mode": "sync"},
        headers={**auth_headers, "Idempotency-Key": _idem()},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["state"] == "succeeded"
    assert body["programme_prior"] == ["talent"]
    assert len(body["groups"]) == 1
    items = body["groups"][0]["items"]
    # закрытая opportunity отфильтрована
    assert [i["opportunity"]["opportunity_id"] for i in items] == [open_id]
    assert items[0]["label"] == "excellent"  # 0.9 >= 0.8
    assert items[0]["liked"] is False and items[0]["hidden"] is False
    # matcher получил один вызов
    assert len(fake_matcher.calls) == 1


@pytest.mark.asyncio
async def test_idempotency_returns_same_run(client, auth_headers, fake_matcher, catalog_opps):
    open_id, _ = catalog_opps
    fake_matcher.response = {
        "programme_prior": ["talent"],
        "groups": [{"programme_kind": "talent", "total_candidates": 1, "items": [
            {"opportunity_id": open_id, "score": 0.9, "breakdown": {}, "reasons": []},
        ]}],
    }
    await _setup_profile(client, auth_headers)
    key = _idem()
    h = {**auth_headers, "Idempotency-Key": key}

    r1 = await client.post("/api/v1/recommendations", json={"mode": "sync"}, headers=h)
    r2 = await client.post("/api/v1/recommendations", json={"mode": "sync"}, headers=h)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["run_id"] == r2.json()["run_id"]
    assert len(fake_matcher.calls) == 1  # второй раз matcher не звали


@pytest.mark.asyncio
async def test_hidden_excluded_from_payload(client, auth_headers, fake_matcher, catalog_opps):
    open_id, _ = catalog_opps
    await _setup_profile(client, auth_headers)

    # юзер скрыл opportunity
    r = await client.post(
        "/api/v1/feedback",
        json={"opportunity_id": open_id, "signal": "hidden"},
        headers=auth_headers,
    )
    assert r.status_code == 204, r.text

    fake_matcher.response = {"groups": [], "programme_prior": []}
    r = await client.post(
        "/api/v1/recommendations",
        json={"mode": "sync"},
        headers={**auth_headers, "Idempotency-Key": _idem()},
    )
    assert r.status_code == 200
    payload = fake_matcher.calls[0]
    assert open_id in payload["filters"]["exclude_opportunity_ids"]


@pytest.mark.asyncio
async def test_matcher_failure_records_failed_run(client, auth_headers, fake_matcher):
    await _setup_profile(client, auth_headers)
    fake_matcher.raise_exc = MatcherTimeout()

    r = await client.post(
        "/api/v1/recommendations",
        json={"mode": "sync"},
        headers={**auth_headers, "Idempotency-Key": _idem()},
    )
    # MatcherTimeout — Problem с 504
    assert r.status_code == 504
    assert r.json()["type"] == "/problems/matcher-timeout"


@pytest.mark.asyncio
async def test_async_mode_returns_202(client, auth_headers, fake_matcher, catalog_opps):
    open_id, _ = catalog_opps
    fake_matcher.response = {"programme_prior": [], "groups": []}
    await _setup_profile(client, auth_headers)

    r = await client.post(
        "/api/v1/recommendations",
        json={"mode": "async"},
        headers={**auth_headers, "Idempotency-Key": _idem()},
    )
    assert r.status_code == 202


@pytest.mark.asyncio
async def test_latest_without_runs(client, auth_headers):
    r = await client.get("/api/v1/recommendations/latest", headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["type"] == "/problems/run-not-found"


@pytest.mark.asyncio
async def test_get_run_other_user_not_found(client, auth_headers, fake_matcher, catalog_opps):
    open_id, _ = catalog_opps
    fake_matcher.response = {"programme_prior": [], "groups": []}
    await _setup_profile(client, auth_headers)
    r = await client.post(
        "/api/v1/recommendations", json={"mode": "sync"},
        headers={**auth_headers, "Idempotency-Key": _idem()},
    )
    run_id = r.json()["run_id"]

    # чужой юзер
    other_email = f"other{uuid.uuid4().hex[:8]}@test.io"
    ro = await client.post(
        "/api/v1/auth/register",
        json={"email": other_email, "password": "Passw0rd!"},
    )
    oh = {"Authorization": f"Bearer {ro.json()['access_token']}"}
    r = await client.get(f"/api/v1/recommendations/{run_id}", headers=oh)
    assert r.status_code == 404