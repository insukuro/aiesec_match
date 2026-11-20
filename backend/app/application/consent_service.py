from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import ConsentRequired, ConsentVersionOutdated, Validation
from ..formschema import load_consent_schema
from ..infrastructure.repositories.consent_repo import ConsentRepo


class ConsentService:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._repo = ConsentRepo(session)

    async def require(self, user_id, kind: str = "pd_processing") -> None:
        document = self._document(kind)
        if not await self._repo.has(user_id, kind, document["version"]):
            raise ConsentRequired()

    async def add(self, user_id, kind: str, version: str) -> None:
        document = self._document(kind)
        if version != document["version"]:
            raise ConsentVersionOutdated()
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

    @staticmethod
    def _document(kind: str) -> dict:
        documents = load_consent_schema()["consents"]
        document = next((item for item in documents if item["kind"] == kind), None)
        if document is None:
            raise Validation(errors=[{
                "loc": ["body", "kind"],
                "msg": "unknown_consent_kind",
            }])
        return document