import pytest

from tests.conftest import VALID_PROFILE


@pytest.mark.asyncio
async def test_get_me_profile_not_found(client, auth_headers):
    r = await client.get("/api/v1/profiles/me", headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["type"] == "/problems/profile-not-found"


@pytest.mark.asyncio
async def test_put_profile_without_consent(client, auth_headers):
    r = await client.put("/api/v1/profiles/me", json=VALID_PROFILE, headers=auth_headers)
    assert r.status_code == 403
    assert r.json()["type"] == "/problems/consent-required"


@pytest.mark.asyncio
async def test_put_profile_creates_v1(client, user_with_consent, monkeypatch):
    from app.application.auth_service import issue_token
    user, _ = user_with_consent
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.put("/api/v1/profiles/me", json=VALID_PROFILE, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["profile_version"] == 1
    assert body["age_years"] is not None
    assert body["completeness"] > 0
    assert r.headers["ETag"] == '"1"'


@pytest.mark.asyncio
async def test_put_profile_increments_version(client, user_with_consent):
    from app.application.auth_service import issue_token
    user, _ = user_with_consent
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    r1 = await client.put("/api/v1/profiles/me", json=VALID_PROFILE, headers=h)
    assert r1.status_code == 200
    r2 = await client.put("/api/v1/profiles/me", json=VALID_PROFILE, headers=h)
    assert r2.status_code == 200
    assert r2.json()["profile_version"] == 2
    assert r2.headers["ETag"] == '"2"'


@pytest.mark.asyncio
async def test_put_profile_if_match_conflict(client, user_with_consent):
    from app.application.auth_service import issue_token
    user, _ = user_with_consent
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    await client.put("/api/v1/profiles/me", json=VALID_PROFILE, headers=h)  # v1
    h_conflict = {**h, "If-Match": '"99"'}
    r = await client.put("/api/v1/profiles/me", json=VALID_PROFILE, headers=h_conflict)
    assert r.status_code == 412
    assert r.json()["type"] == "/problems/version-conflict"


@pytest.mark.asyncio
async def test_put_profile_if_match_ok(client, user_with_consent):
    from app.application.auth_service import issue_token
    user, _ = user_with_consent
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    await client.put("/api/v1/profiles/me", json=VALID_PROFILE, headers=h)  # v1
    h_ok = {**h, "If-Match": '"1"'}
    r = await client.put("/api/v1/profiles/me", json=VALID_PROFILE, headers=h_ok)
    assert r.status_code == 200
    assert r.json()["profile_version"] == 2


@pytest.mark.asyncio
async def test_put_profile_invalid_age(client, user_with_consent):
    from app.application.auth_service import issue_token
    user, _ = user_with_consent
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    bad = {**VALID_PROFILE, "birth_date": "2020-01-01"}  # 6 лет
    r = await client.put("/api/v1/profiles/me", json=bad, headers=h)
    assert r.status_code == 422
    assert any("birth_date_too_young" in e["msg"] for e in r.json()["errors"])


@pytest.mark.asyncio
async def test_get_profile_returns_etag(client, user_with_profile):
    from app.application.auth_service import issue_token
    user, _ = user_with_profile
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.get("/api/v1/profiles/me", headers=h)
    assert r.status_code == 200
    assert r.headers["ETag"] == '"1"'
    assert r.json()["profile_version"] == 1


@pytest.mark.asyncio
async def test_list_versions_desc(client, user_with_profile):
    from app.application.auth_service import issue_token
    user, _ = user_with_profile
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.get("/api/v1/profiles/me/versions", headers=h)
    assert r.status_code == 200
    versions = [v["version"] for v in r.json()]
    assert versions == sorted(versions, reverse=True)
    assert 1 in versions


@pytest.mark.asyncio
async def test_get_version_snapshot(client, user_with_profile):
    from app.application.auth_service import issue_token
    user, _ = user_with_profile
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.get("/api/v1/profiles/me/versions/1", headers=h)
    assert r.status_code == 200
    assert r.json()["version"] == 1


@pytest.mark.asyncio
async def test_get_version_not_found(client, user_with_profile):
    from app.application.auth_service import issue_token
    user, _ = user_with_profile
    tok, _ = issue_token(user.user_id, 3600)
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.get("/api/v1/profiles/me/versions/999", headers=h)
    assert r.status_code == 404

