from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import LinkCode


class LinkCodeRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def get(self, code: str) -> LinkCode | None:
        return await self._s.get(LinkCode, code)

    async def create(
        self, code: str, user_id: uuid.UUID, expires_at: datetime,
    ) -> LinkCode:
        lc = LinkCode(code=code, user_id=user_id, expires_at=expires_at)
        self._s.add(lc)
        return lc

    async def mark_used(self, code: LinkCode) -> None:
        code.used_at = datetime.now(timezone.utc)