import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_session
from .errors import ForbiddenGuest, Unauthorized
from .models import DeviceSecret, Identity, PasswordCredential, User

bearer = HTTPBearer(auto_error=False)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def hash_password(raw: str) -> str:
    return pwd_ctx.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(raw, hashed)
    except ValueError:
        return False


def issue_token(user_id: uuid.UUID, ttl: int, aud: str = "client") -> tuple[str, int]:
    s = get_settings()
    exp = _now() + timedelta(seconds=ttl)
    tok = jwt.encode(
        {"sub": str(user_id), "exp": exp, "aud": aud, "iat": _now()},
        s.jwt_secret, algorithm="HS256",
    )
    return tok, ttl


async def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if creds is None:
        raise Unauthorized()
    try:
        payload = jwt.decode(
            creds.credentials, get_settings().jwt_secret,
            algorithms=["HS256"], audience="client",
        )
    except jwt.PyJWTError as e:
        raise Unauthorized(str(e)) from e
    uid = uuid.UUID(payload["sub"])
    user = await session.get(User, uid)
    if user is None or user.deleted_at is not None:
        raise Unauthorized()
    return user


async def require_registered(user: User = Depends(current_user)) -> User:
    """Гость не имеет доступа к профилю/подбору/истории."""
    if user.is_anonymous:
        raise ForbiddenGuest()
    return user


def hash_device_secret(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def resolve_or_create_anonymous(
    session: AsyncSession, raw_secret: str | None,
) -> tuple[User, str | None]:
    if raw_secret:
        h = hash_device_secret(raw_secret)
        row = (await session.execute(
            select(DeviceSecret).where(DeviceSecret.secret_hash == h)
        )).scalar_one_or_none()
        if row:
            user = await session.get(User, row.user_id)
            if user and user.deleted_at is None and user.is_anonymous:
                return user, None

    user = User(is_anonymous=True)
    session.add(user)
    await session.flush()
    session.add(Identity(user_id=user.user_id, provider="anonymous"))
    new_secret = secrets.token_urlsafe(32)
    session.add(DeviceSecret(user_id=user.user_id, secret_hash=hash_device_secret(new_secret)))
    await session.commit()
    return user, new_secret


async def register_with_password(
    session: AsyncSession, email: str, password: str,
) -> User:
    email_norm = email.strip().lower()
    exists = (await session.execute(
        select(PasswordCredential).where(PasswordCredential.email == email_norm)
    )).scalar_one_or_none()
    if exists is not None:
        raise ValueError("email_taken")
    user = User(is_anonymous=False)
    session.add(user)
    await session.flush()
    session.add(Identity(user_id=user.user_id, provider="password", external_id=email_norm))
    session.add(PasswordCredential(
        user_id=user.user_id, email=email_norm, password_hash=hash_password(password),
    ))
    await session.commit()
    return user


async def login_with_password(
    session: AsyncSession, email: str, password: str,
) -> User | None:
    email_norm = email.strip().lower()
    cred = (await session.execute(
        select(PasswordCredential).where(PasswordCredential.email == email_norm)
    )).scalar_one_or_none()
    if cred is None:
        return None
    if not verify_password(password, cred.password_hash):
        return None
    user = await session.get(User, cred.user_id)
    if user is None or user.deleted_at is not None:
        return None
    return user


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