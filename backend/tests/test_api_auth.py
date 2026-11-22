import pytest
import uuid

from app.config import get_settings

@pytest.mark.asyncio
async def test_register_returns_token(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": f"new{uuid.uuid4().hex[:8]}@test.io", "password": "Passw0rd!"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"]
    me = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    email = f"dup{uuid.uuid4().hex[:8]}@test.io"
    payload = {"email": email, "password": "Passw0rd!"}
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 200
    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert r2.json()["type"] == "/problems/email-taken"

@pytest.mark.asyncio
async def test_register_weak_password(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@test.io", "password": "onlyletters"},
    )
    assert r.status_code == 422
    assert r.json()["type"] == "/problems/validation"
    assert any("password_weak" in e["msg"] for e in r.json()["errors"])


@pytest.mark.asyncio
async def test_register_short_password(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@test.io", "password": "Ab1"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_ok(client):
    email = "login@test.io"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd!"},
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Passw0rd!"},
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    email = "wrongpw@test.io"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd!"},
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPass1"},
    )
    assert r.status_code == 401
    assert r.json()["type"] == "/problems/bad-credentials"


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.io", "password": "Passw0rd!"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_email_case_insensitive(client):
    email = "Case@Test.IO"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd!"},
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email.lower(), "password": "Passw0rd!"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_telegram_creates_user_and_is_idempotent(client, monkeypatch):
    import hashlib
    import hmac
    import json
    import time
    from urllib.parse import urlencode

    bot_token = "123:ABC"
    monkeypatch.setenv("AIESEC_TELEGRAM_BOT_TOKEN", bot_token)
    get_settings_cached = __import__("app.config", fromlist=["get_settings"]).get_settings
    get_settings_cached.cache_clear()

    def make_init_data(user: dict) -> str:
        pairs = {
            "user": json.dumps(user, separators=(",", ":")),
            "auth_date": str(int(time.time())),
        }
        check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hashlib.sha256(bot_token.encode()).digest()
        pairs["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        return urlencode(pairs)

    user = {"id": 777, "first_name": "TG"}
    init = make_init_data(user)

    r1 = await client.post("/api/v1/auth/telegram", json={"init_data": init})
    assert r1.status_code == 200, r1.text
    uid1 = (await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {r1.json()['access_token']}"},
    )).json()["user_id"]

    # Повторный вход тем же telegram id — не создаёт нового юзера
    init2 = make_init_data(user)
    r2 = await client.post("/api/v1/auth/telegram", json={"init_data": init2})
    assert r2.status_code == 200
    uid2 = (await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {r2.json()['access_token']}"},
    )).json()["user_id"]
    assert uid1 == uid2

    # identity сохранена
    me = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {r2.json()['access_token']}"},
    )
    providers = [i["provider"] for i in me.json()["identities"]]
    assert "telegram" in providers


@pytest.mark.asyncio
async def test_telegram_bad_signature(client, monkeypatch):
    monkeypatch.setenv("AIESEC_TELEGRAM_BOT_TOKEN", "123:ABC")
    __import__("app.config", fromlist=["get_settings"]).get_settings.cache_clear()

    r = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": "user=%7B%22id%22%3A1%7D&auth_date=1&hash=deadbeef"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_is_unauthorized(client):
    r = await client.get("/api/v1/me")
    assert r.status_code == 401
    assert r.json()["type"] == "/problems/unauthorized"


@pytest.mark.asyncio
async def test_me_with_garbage_token_is_unauthorized(client):
    r = await client.get("/api/v1/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_deleted_account_token_is_unauthorized(client):
    email = f"deleted{uuid.uuid4().hex[:8]}@test.io"
    registered = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd!"},
    )
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    deleted = await client.delete("/api/v1/me", headers=headers)
    assert deleted.status_code == 204

    r = await client.get("/api/v1/history", headers=headers)
    assert r.status_code == 401
    assert r.json()["type"] == "/problems/unauthorized"


@pytest.mark.asyncio
async def test_email_change_requires_delivery_configuration(client, monkeypatch):
    monkeypatch.setenv("AIESEC_DEV_MODE", "false")
    get_settings.cache_clear()
    try:
        email = f"mail{uuid.uuid4().hex[:8]}@test.io"
        registered = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Passw0rd!"},
        )
        headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
        r = await client.post(
            "/api/v1/auth/change-email",
            json={"new_email": f"next{uuid.uuid4().hex[:8]}@test.io", "password": "Passw0rd!"},
            headers=headers,
        )
        assert r.status_code == 503
        assert r.json()["type"] == "/problems/email-delivery-unavailable"
        assert "dev_code" not in r.json()
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_email_change_development_verification_flow(client, monkeypatch):
    monkeypatch.setenv("AIESEC_DEV_MODE", "true")
    get_settings.cache_clear()
    try:
        email = f"old{uuid.uuid4().hex[:8]}@test.io"
        next_email = f"new{uuid.uuid4().hex[:8]}@test.io"
        registered = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Passw0rd!"},
        )
        headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
        requested = await client.post(
            "/api/v1/auth/change-email",
            json={"new_email": next_email, "password": "Passw0rd!"},
            headers=headers,
        )
        assert requested.status_code == 200
        code = requested.json()["dev_code"]

        verified = await client.post(
            "/api/v1/auth/verify-email",
            params={"new_email": next_email},
            json={"code": code},
            headers=headers,
        )
        assert verified.status_code == 204
        me = await client.get("/api/v1/me", headers=headers)
        assert me.json()["email"] == next_email
        assert me.json()["email_verified"] is True
    finally:
        get_settings.cache_clear()