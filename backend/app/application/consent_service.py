from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import ConsentRequired, Validation
from ..infrastructure.repositories.consent_repo import ConsentRepo


class ConsentService:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._repo = ConsentRepo(session)

    async def require(self, user_id, kind: str = "pd_processing") -> None:
        if not await self._repo.has(user_id, kind):
            raise ConsentRequired()

    async def add(self, user_id, kind: str, version: str) -> None:
        await self._repo.add(user_id, kind, version)
        await self._s.commit()

    async def revoke(self, user_id, kind: str) -> None:
        if kind == "pd_processing":
            raise Validation(errors=[{
                "loc": ["path", "kind"],
                "msg": "pd_processing_cannot_be_revoked",
            }])
        await self._repo.revoke(user_id, kind)
        await self._s.commit()