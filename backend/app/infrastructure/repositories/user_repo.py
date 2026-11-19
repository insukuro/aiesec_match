from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EmailVerification, Identity, PasswordCredential, User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        u = await self._s.get(User, user_id)
        if u is None or u.deleted_at is not None:
            return None
        return u

    async def get_by_email(self, email: str) -> PasswordCredential | None:
        return (await self._s.execute(
            select(PasswordCredential).where(PasswordCredential.email == email)
        )).scalar_one_or_none()

    async def get_credential(self, user_id: uuid.UUID) -> PasswordCredential | None:
        return await self._s.get(PasswordCredential, user_id)

    async def get_identity(self, provider: str, external_id: str) -> Identity | None:
        return (await self._s.execute(
            select(Identity).where(
                Identity.provider == provider,
                Identity.external_id == external_id,
            )
        )).scalar_one_or_none()

    async def create(self) -> User:
        u = User()
        self._s.add(u)
        await self._s.flush()
        return u

    async def add_password_credential(
        self, user_id: uuid.UUID, email: str, password_hash: str,
    ) -> None:
        self._s.add(PasswordCredential(
            user_id=user_id, email=email, password_hash=password_hash,
        ))

    async def add_identity(
        self, user_id: uuid.UUID, provider: str, external_id: str | None = None,
    ) -> None:
        self._s.add(Identity(user_id=user_id, provider=provider, external_id=external_id))

    async def soft_delete(self, user: User) -> None:
        user.deleted_at = datetime.now(timezone.utc)

    async def identities_for(self, user_id: uuid.UUID) -> list[Identity]:
        return list((await self._s.execute(
            select(Identity).where(Identity.user_id == user_id)
        )).scalars().all())

    # ---------- email verification ----------

    async def get_verification(self, user_id: uuid.UUID) -> EmailVerification | None:
        return (await self._s.execute(
            select(EmailVerification).where(EmailVerification.user_id == user_id)
        )).scalar_one_or_none()

    async def upsert_verification(
        self, user_id: uuid.UUID, code_hash: str, expires_at: datetime,
    ) -> EmailVerification:
        v = await self.get_verification(user_id)
        if v is None:
            v = EmailVerification(
                user_id=user_id, code_hash=code_hash, expires_at=expires_at,
            )
            self._s.add(v)
        else:
            v.code_hash = code_hash
            v.expires_at = expires_at
        return v

    async def delete_verification(self, user_id: uuid.UUID) -> None:
        v = await self.get_verification(user_id)
        if v is not None:
            await self._s.delete(v)