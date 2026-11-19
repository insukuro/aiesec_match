from __future__ import annotations

import asyncio
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..errors import (
    BadCredentials, EmailChangePending, EmailTaken, EmailNotVerified,
    InvalidVerificationCode, Unauthorized, Validation,
)
from ..infrastructure.repositories.user_repo import UserRepo
from ..infrastructure.telegram_adapter import verify_init_data

_bcrypt_sem = asyncio.Semaphore(8)


def _hash_password_sync(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def _verify_password_sync(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode(), hashed.encode())
    except ValueError:
        return False


async def hash_password(raw: str) -> str:
    async with _bcrypt_sem:
        return await asyncio.to_thread(_hash_password_sync, raw)


async def verify_password(raw: str, hashed: str) -> bool:
    async with _bcrypt_sem:
        return await asyncio.to_thread(_verify_password_sync, raw, hashed)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def issue_token(user_id: uuid.UUID, ttl: int, aud: str = "client") -> tuple[str, int]:
    s = get_settings()
    exp = _now() + timedelta(seconds=ttl)
    tok = jwt.encode(
        {"sub": str(user_id), "exp": exp, "aud": aud, "iat": _now()},
        s.jwt_secret, algorithm="HS256",
    )
    return tok, ttl


def decode_token(raw: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            raw, get_settings().jwt_secret,
            algorithms=["HS256"], audience="client",
        )
    except jwt.PyJWTError as e:
        raise Unauthorized(str(e)) from e
    return uuid.UUID(payload["sub"])


def _verification_code_hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


class AuthService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = UserRepo(session)

    # ---------- register / login ----------

    async def register(self, email: str, password: str):
        email_norm = email.strip().lower()
        if await self._users.get_by_email(email_norm) is not None:
            raise EmailTaken()
        password_hash = await hash_password(password)
        user = await self._users.create()
        await self._users.add_identity(user.user_id, "password", email_norm)
        await self._users.add_password_credential(user.user_id, email_norm, password_hash)
        await self._session.commit()
        token, ttl = issue_token(user.user_id, get_settings().jwt_ttl_seconds)
        return token, ttl

    async def login(self, email: str, password: str):
        email_norm = email.strip().lower()
        cred = await self._users.get_by_email(email_norm)
        if cred is None or not await verify_password(password, cred.password_hash):
            raise BadCredentials()
        user = await self._users.get(cred.user_id)
        if user is None:
            raise BadCredentials()
        token, ttl = issue_token(user.user_id, get_settings().jwt_ttl_seconds)
        return token, ttl

    async def telegram(self, init_data: str):
        info = verify_init_data(init_data, get_settings().telegram_bot_token)
        ext = str(info["id"])
        ident = await self._users.get_identity("telegram", ext)
        if ident is None:
            user = await self._users.create()
            await self._users.add_identity(user.user_id, "telegram", ext)
            await self._session.commit()
        else:
            user = await self._users.get(ident.user_id)
            if user is None:
                raise BadCredentials()
        token, ttl = issue_token(user.user_id, get_settings().jwt_ttl_seconds)
        return token, ttl

    # ---------- change password ----------

    async def change_password(
        self, user_id: uuid.UUID, current_password: str, new_password: str,
    ) -> None:
        cred = await self._users.get_credential(user_id)
        if cred is None:
            raise Validation(errors=[{
                "loc": ["body", "current_password"],
                "msg": "password_login_not_configured",
            }])
        if not await verify_password(current_password, cred.password_hash):
            raise BadCredentials()
        cred.password_hash = await hash_password(new_password)
        cred.updated_at = _now()
        await self._session.commit()

    # ---------- change email (с верификацией) ----------

    async def request_email_change(
        self, user_id: uuid.UUID, new_email: str, password: str,
    ) -> str:
        """Возвращает код, который в проде уходит письмом (здесь — в ответе)."""
        cred = await self._users.get_credential(user_id)
        if cred is None:
            raise Validation(errors=[{
                "loc": ["body", "password"],
                "msg": "password_login_not_configured",
            }])
        if not await verify_password(password, cred.password_hash):
            raise BadCredentials()
        new_email_norm = new_email.strip().lower()
        if new_email_norm == cred.email:
            raise Validation(errors=[{
                "loc": ["body", "new_email"],
                "msg": "email_unchanged",
            }])
        if await self._users.get_by_email(new_email_norm) is not None:
            raise EmailTaken()

        # Проверяем, нет ли уже активной заявки на смену email у другого/этого пользователя.
        # Простейший вариант: одна заявка на user_id, а код хранит new_email в коде.
        # Для MVP: сохраняем хеш кода в email_verifications и держим new_email в
        # in-memory/Redis; в текущем коде кладём new_email в код (base64) — но это
        # небезопасно. Ниже — корректный вариант через отдельную колонку.
        # Требуется миграция 0007 или используем «код = hmac(code + new_email)».
        # Мы используем: code_hash = sha256(code), а new_email передаётся в verify.
        # Тогда клиент должен передать и new_email, и code.
        code = f"{secrets.randbelow(10**6):06d}"
        expires_at = _now() + timedelta(minutes=15)
        await self._users.upsert_verification(
            user_id, _verification_code_hash(code + new_email_norm), expires_at,
        )
        await self._session.commit()
        return code

    async def verify_email_change(
        self, user_id: uuid.UUID, new_email: str, code: str,
    ) -> None:
        new_email_norm = new_email.strip().lower()
        v = await self._users.get_verification(user_id)
        if v is None or v.expires_at < _now():
            raise InvalidVerificationCode()
        if v.code_hash != _verification_code_hash(code + new_email_norm):
            raise InvalidVerificationCode()
        cred = await self._users.get_credential(user_id)
        if cred is None:
            raise Validation(errors=[{
                "loc": ["body", "code"],
                "msg": "password_login_not_configured",
            }])
        # На случай гонки — ещё раз проверим уникальность.
        existing = await self._users.get_by_email(new_email_norm)
        if existing is not None and existing.user_id != user_id:
            raise EmailTaken()
        cred.email = new_email_norm
        cred.email_verified_at = _now()
        cred.updated_at = _now()
        # Обновляем identity(password), чтобы логин и /me показывали новый email.
        for ident in await self._users.identities_for(user_id):
            if ident.provider == "password":
                ident.external_id = new_email_norm
        await self._users.delete_verification(user_id)
        await self._session.commit()