from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Consent


class ConsentRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def has(self, user_id: uuid.UUID, kind: str) -> bool:
        row = (await self._s.execute(
            select(Consent).where(Consent.user_id == user_id, Consent.kind == kind)
        )).scalar_one_or_none()
        return row is not None

    async def list_for(self, user_id: uuid.UUID) -> list[Consent]:
        return list((await self._s.execute(
            select(Consent).where(Consent.user_id == user_id)
        )).scalars().all())

    async def add(self, user_id: uuid.UUID, kind: str, version: str) -> None:
        existing = await self._s.get(Consent, (user_id, kind, version))
        if existing is None:
            self._s.add(Consent(user_id=user_id, kind=kind, version=version))

    async def revoke(self, user_id: uuid.UUID, kind: str) -> int:
        result = await self._s.execute(
            delete(Consent).where(Consent.user_id == user_id, Consent.kind == kind)
        )
        return result.rowcount or 0