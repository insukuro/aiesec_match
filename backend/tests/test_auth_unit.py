# backend/tests/test_auth_unit.py
import hashlib
import hmac
import time
import uuid
from urllib.parse import urlencode

import jwt
import pytest

from app.auth import (
    hash_device_secret,
    hash_password,
    issue_token,
    verify_password,
    verify_telegram_init_data,
)
from app.config import get_settings
from app.errors import Unauthorized


@pytest.mark.asyncio
async def test_hash_and_verify_password_roundtrip():
    h = await hash_password("secret123")
    assert h != "secret123"
    assert await verify_password("secret123", h) is True
    assert await verify_password("wrong", h) is False


@pytest.mark.asyncio
async def test_verify_password_bad_hash_no_raise():
    assert await verify_password("x", "not-a-bcrypt-hash") is False


def test_hash_device_secret_stable():
    assert hash_device_secret("abc") == hashlib.sha256(b"abc").hexdigest()


def test_issue_token_roundtrip():
    uid = uuid.uuid4()
    tok, ttl = issue_token(uid, 60)
    assert ttl == 60
    payload = jwt.decode(tok, get_settings().jwt_secret,
                         algorithms=["HS256"], audience="client")
    assert payload["sub"] == str(uid)


def test_issue_token_bad_audience_fails():
    tok, _ = issue_token(uuid.uuid4(), 60, aud="other")
    with pytest.raises(jwt.InvalidAudienceError):
        jwt.decode(tok, get_settings().jwt_secret,
                   algorithms=["HS256"], audience="client")


def _make_init_data(bot_token: str, user: dict, auth_date: int | None = None) -> str:
    pairs = {"user": __import__("json").dumps(user, separators=(",", ":"))}
    pairs["auth_date"] = str(auth_date or int(time.time()))
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hashlib.sha256(bot_token.encode()).digest()
    h = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    pairs["hash"] = h
    return urlencode(pairs)


def test_telegram_init_data_ok():
    token = "123:ABC"
    user = {"id": 42, "first_name": "Test"}
    data = _make_init_data(token, user)
    out = verify_telegram_init_data(data, token)
    assert out["id"] == 42


def test_telegram_bad_signature():
    token = "123:ABC"
    data = _make_init_data(token, {"id": 42})
    with pytest.raises(Unauthorized):
        verify_telegram_init_data(data, "other:token")


def test_telegram_expired():
    token = "123:ABC"
    old = int(time.time()) - 25 * 3600
    data = _make_init_data(token, {"id": 42}, auth_date=old)
    with pytest.raises(Unauthorized, match="expired"):
        verify_telegram_init_data(data, token)