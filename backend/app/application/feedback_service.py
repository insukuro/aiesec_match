from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import Validation
from ..infrastructure.repositories.catalog_repo import CatalogRepo
from ..infrastructure.repositories.feedback_repo import FeedbackRepo
from ..schemas import FeedbackIn
from .dto_mappers import card_dto

VALID_SIGNALS = {"opened", "liked", "disliked", "hidden", "applied"}


class FeedbackService:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._repo = FeedbackRepo(session)
        self._catalog = CatalogRepo(session)

    async def create(self, user_id, body: FeedbackIn) -> None:
        if body.signal not in VALID_SIGNALS:
            raise Validation(errors=[{"loc": ["body", "signal"], "msg": "invalid signal"}])
        run_id = uuid.UUID(body.run_id) if body.run_id else None
        await self._repo.add(user_id, body.opportunity_id, body.signal, run_id)
        await self._s.commit()

    async def remove(self, user_id, opportunity_id: int, signal: str) -> None:
        await self._repo.remove(user_id, opportunity_id, signal)
        await self._s.commit()

    async def list_liked(self, user_id, limit: int, offset: int) -> dict:
        return await self._list_by_signals(user_id, ["liked"], limit, offset)

    async def list_hidden(self, user_id, limit: int, offset: int) -> dict:
        return await self._list_by_signals(user_id, ["hidden", "disliked"], limit, offset)

    async def _list_by_signals(
        self, user_id, signals: list[str], limit: int, offset: int,
    ) -> dict:
        opp_ids, total = await self._repo.paged_ids(user_id, signals, limit, offset)
        cards = await self._catalog.fetch_cards(opp_ids)
        reqs = await self._catalog.fetch_requirements(opp_ids)
        items = [
            card_dto(cards[oid], reqs.get(oid, []))
            for oid in opp_ids
            if oid in cards
        ]
        return {"items": items, "total": total, "limit": limit, "offset": offset}