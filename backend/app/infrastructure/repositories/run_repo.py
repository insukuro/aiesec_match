from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import RecommendationItem, RecommendationRun


class RunRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def get(self, run_id: uuid.UUID) -> RecommendationRun | None:
        return await self._s.get(RecommendationRun, run_id)

    async def get_by_idempotency(
        self, user_id: uuid.UUID, key: str,
    ) -> RecommendationRun | None:
        return (await self._s.execute(
            select(RecommendationRun).where(
                RecommendationRun.user_id == user_id,
                RecommendationRun.idempotency_key == key,
            )
        )).scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        profile_version: int,
        filters: dict,
        idempotency_key: str,
    ) -> RecommendationRun:
        run = RecommendationRun(
            user_id=user_id,
            profile_version=profile_version,
            filters=filters or {},
            idempotency_key=idempotency_key,
            state="running",
            model_versions={},
        )
        self._s.add(run)
        await self._s.flush()
        return run

    async def items_for(self, run_id: uuid.UUID) -> list[RecommendationItem]:
        return list((await self._s.execute(
            select(RecommendationItem)
            .where(RecommendationItem.run_id == run_id)
            .order_by(RecommendationItem.programme_kind, RecommendationItem.rank)
        )).scalars().all())

    async def add_item(
        self,
        run_id: uuid.UUID,
        programme_kind: str,
        rank: int,
        opportunity_id: int,
        family_key: str | None,
        score: float,
        breakdown: dict[str, Any],
        reasons: list[dict],
    ) -> None:
        self._s.add(RecommendationItem(
            run_id=run_id,
            programme_kind=programme_kind,
            rank=rank,
            opportunity_id=opportunity_id,
            family_key=family_key,
            score=score,
            breakdown=breakdown or {},
            reasons=reasons or [],
        ))

    async def latest_succeeded(self, user_id: uuid.UUID) -> RecommendationRun | None:
        return (await self._s.execute(
            select(RecommendationRun)
            .where(
                RecommendationRun.user_id == user_id,
                RecommendationRun.state == "succeeded",
            )
            .order_by(RecommendationRun.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

    async def list_for_user(
        self, user_id: uuid.UUID, limit: int, offset: int,
    ) -> tuple[list[RecommendationRun], int]:
        total = (await self._s.execute(
            select(func.count()).select_from(RecommendationRun).where(
                RecommendationRun.user_id == user_id
            )
        )).scalar_one()
        rows = (await self._s.execute(
            select(RecommendationRun)
            .where(RecommendationRun.user_id == user_id)
            .order_by(RecommendationRun.created_at.desc())
            .limit(limit).offset(offset)
        )).scalars().all()
        return list(rows), int(total)