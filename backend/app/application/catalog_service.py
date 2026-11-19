from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import OpportunityNotFound
from ..infrastructure.repositories.catalog_repo import CatalogRepo
from ..schemas import Page
from .dto_mappers import card_dto


class CatalogService:
    def __init__(self, session: AsyncSession):
        self._repo = CatalogRepo(session)

    async def list(
        self,
        *,
        q, programme_kind, country_code, lc_id, family_key,
        only_open, sort, limit, offset,
    ) -> Page:
        rows, total = await self._repo.list_opportunities(
            q=q, programme_kind=programme_kind, country_code=country_code,
            lc_id=lc_id, family_key=family_key, only_open=only_open,
            sort=sort, limit=limit, offset=offset,
        )
        ids = [r.opportunity_id for r in rows]
        reqs = await self._repo.fetch_requirements(ids)
        items = [card_dto(r, reqs.get(r.opportunity_id, [])) for r in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)

    async def detail(self, opportunity_id: int) -> dict:
        cards = await self._repo.fetch_cards([opportunity_id])
        if not cards:
            raise OpportunityNotFound()
        reqs = await self._repo.fetch_requirements([opportunity_id])
        c = cards[opportunity_id]
        dto = card_dto(c, reqs.get(opportunity_id, []))
        dto.update({
            "earliest_start_date": c.earliest_start_date,
            "latest_end_date": c.latest_end_date,
            "experience_type": c.experience_type,
            "close_reason": c.close_reason,
            "family": {"family_key": c.family_key, "siblings_count": 0},
        })
        return dto