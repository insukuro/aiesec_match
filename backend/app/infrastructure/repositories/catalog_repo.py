from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import OpportunityRequirementV1, OpportunityV1, SyncStateV1


class CatalogRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def fetch_cards(self, ids: list[int]) -> dict[int, OpportunityV1]:
        if not ids:
            return {}
        rows = (await self._s.execute(
            select(OpportunityV1).where(OpportunityV1.opportunity_id.in_(ids))
        )).scalars().all()
        return {r.opportunity_id: r for r in rows}

    async def fetch_requirements(self, ids: list[int]) -> dict[int, list[OpportunityRequirementV1]]:
        if not ids:
            return {}
        rows = (await self._s.execute(
            select(OpportunityRequirementV1).where(
                OpportunityRequirementV1.opportunity_id.in_(ids)
            )
        )).scalars().all()
        out: dict[int, list[OpportunityRequirementV1]] = {}
        for r in rows:
            out.setdefault(r.opportunity_id, []).append(r)
        return out

    async def list_opportunities(
        self, *,
        q: str | None,
        programme_kind: str | None,
        country_code: str | None,
        lc_id: int | None,
        family_key: str | None,
        only_open: bool,
        sort: str,
        limit: int,
        offset: int,
    ) -> tuple[list[OpportunityV1], int]:
        stmt = select(OpportunityV1)
        if q:
            stmt = stmt.where(OpportunityV1.title.ilike(f"%{q}%"))
        if programme_kind:
            stmt = stmt.where(OpportunityV1.programme_kind == programme_kind)
        if country_code:
            stmt = stmt.where(OpportunityV1.country_code == country_code)
        if lc_id is not None:
            stmt = stmt.where(OpportunityV1.lc_id == lc_id)
        if family_key:
            stmt = stmt.where(OpportunityV1.family_key == family_key)
        if only_open:
            stmt = stmt.where(
                OpportunityV1.is_open.is_(True),
                OpportunityV1.available_openings > 0,
            )

        total = (await self._s.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()

        if sort == "closing":
            stmt = stmt.order_by(
                OpportunityV1.applications_close_date.asc().nulls_last(),
                OpportunityV1.opportunity_id.asc(),
            )
        elif sort == "chance":
            ratio = (
                OpportunityV1.available_openings.cast(float)
                / func.greatest(OpportunityV1.applicants_count, 1)
            )
            stmt = stmt.order_by(ratio.desc().nulls_last(), OpportunityV1.opportunity_id)
        else:
            stmt = stmt.order_by(
                OpportunityV1.remote_updated_at.desc().nulls_last(),
                OpportunityV1.opportunity_id.desc(),
            )

        rows = (await self._s.execute(
            stmt.limit(limit).offset(offset)
        )).scalars().all()
        return list(rows), int(total)

    async def current_watermark(self):
        row = (await self._s.execute(
            select(SyncStateV1).limit(1)
        )).scalar_one_or_none()
        return row.committed_watermark if row else None

    async def programme_stats(self) -> list[dict[str, Any]]:
        rows = (await self._s.execute(
            select(
                OpportunityV1.programme_kind,
                func.count().filter(
                    OpportunityV1.is_open.is_(True),
                    OpportunityV1.available_openings > 0,
                ).label("cnt"),
            ).group_by(OpportunityV1.programme_kind)
        )).all()
        return [{"code": r.programme_kind, "count": int(r.cnt or 0)} for r in rows]