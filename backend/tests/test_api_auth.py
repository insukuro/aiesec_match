import pytest
import uuid

@pytest.mark.asyncio
async def test_anonymous_creates_guest(client):
    r = await client.post("/api/v1/auth/anonymous", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"]
    assert body["expires_in"] > 0
    assert body["device_secret"]
    assert body["device_secret"] != ""


@pytest.mark.asyncio
async def test_anonymous_same_secret_returns_same_user(client):
    r1 = await client.post("/api/v1/auth/anonymous", json={})
    secret = r1.json()["device_secret"]

    r2 = await client.post("/api/v1/auth/anonymous", json={"device_secret": secret})
    assert r2.status_code == 200
    # повторный вход с тем же секретом — новый секрет не выдаётся
    assert r2.json()["device_secret"] is None

    # токены указывают на одного и того же юзера
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    me1 = await client.get("/api/v1/me", headers=h1)
    me2 = await client.get("/api/v1/me", headers=h2)
    assert me1.json()["user_id"] == me2.json()["user_id"]
    assert me1.json()["is_anonymous"] is True


@pytest.mark.asyncio
async def test_anonymous_bad_secret_creates_new_user(client):
    r1 = await client.post("/api/v1/auth/anonymous", json={})
    uid1 = (await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {r1.json()['access_token']}"},
    )).json()["user_id"]

    r2 = await client.post("/api/v1/auth/anonymous", json={"device_secret": "garbage"})
    assert r2.status_code == 200
    assert r2.json()["device_secret"]  # новый гость → новый секрет
    uid2 = (await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {r2.json()['access_token']}"},
    )).json()["user_id"]
    assert uid1 != uid2


@pytest.mark.asyncio
async def test_register_returns_token(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": f"new{uuid.uuid4().hex[:8]}@test.io", "password": "Passw0rd!"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_anonymous"] is False
    assert body["access_token"]


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
    assert r.json()["is_anonymous"] is False


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