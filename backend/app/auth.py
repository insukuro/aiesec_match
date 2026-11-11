import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_session
from .errors import Unauthorized
from .models import DeviceSecret, Identity, User

bearer = HTTPBearer(auto_error=False)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def issue_token(user_id: uuid.UUID, ttl: int, aud: str = "client") -> tuple[str, int]:
    s = get_settings()
    exp = _now() + timedelta(seconds=ttl)
    tok = jwt.encode({"sub": str(user_id), "exp": exp, "aud": aud, "iat": _now()},
                     s.jwt_secret, algorithm="HS256")
    return tok, ttl


async def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if creds is None:
        raise Unauthorized()
    try:
        payload = jwt.decode(creds.credentials, get_settings().jwt_secret,
                             algorithms=["HS256"], audience="client")
    except jwt.PyJWTError as e:
        raise Unauthorized(str(e)) from e
    uid = uuid.UUID(payload["sub"])
    user = await session.get(User, uid)
    if user is None or user.deleted_at is not None:
        raise Unauthorized()
    return user


def hash_device_secret(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def resolve_or_create_anonymous(session: AsyncSession, raw_secret: str | None) -> tuple[User, str | None]:
    """Если секрет совпал — вернуть существующего; иначе создать."""
    if raw_secret:
        h = hash_device_secret(raw_secret)
        row = (await session.execute(
            select(DeviceSecret).where(DeviceSecret.secret_hash == h)
        )).scalar_one_or_none()
        if row:
            user = await session.get(User, row.user_id)
            if user and user.deleted_at is None:
                return user, None

    user = User()
    session.add(user)
    await session.flush()
    session.add(Identity(user_id=user.user_id, provider="anonymous"))
    new_secret = secrets.token_urlsafe(32)
    session.add(DeviceSecret(user_id=user.user_id, secret_hash=hash_device_secret(new_secret)))
    await session.commit()
    return user, new_secret


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", "")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hashlib.sha256(bot_token.encode()).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, expected):
        raise Unauthorized("bad initData signature")
    auth_date = int(pairs.get("auth_date", "0"))
    if _now().timestamp() - auth_date > 24 * 3600:
        raise Unauthorized("initData expired")
    return json.loads(pairs["user"])