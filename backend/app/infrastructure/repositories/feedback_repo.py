from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Feedback


class FeedbackRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def add(
        self,
        user_id: uuid.UUID,
        opportunity_id: int,
        signal: str,
        run_id: uuid.UUID | None,
    ) -> None:
        stmt = insert(Feedback).values(
            user_id=user_id,
            run_id=run_id,
            opportunity_id=opportunity_id,
            signal=signal,
        ).on_conflict_do_nothing(
            index_elements=["user_id", "opportunity_id", "signal"],
        )
        await self._s.execute(stmt)

    async def remove(self, user_id: uuid.UUID, opportunity_id: int, signal: str) -> None:
        await self._s.execute(
            delete(Feedback).where(
                Feedback.user_id == user_id,
                Feedback.opportunity_id == opportunity_id,
                Feedback.signal == signal,
            )
        )

    async def ids_by_signals(self, user_id: uuid.UUID, signals: list[str]) -> list[int]:
        return list((await self._s.execute(
            select(Feedback.opportunity_id)
            .where(Feedback.user_id == user_id, Feedback.signal.in_(signals))
            .distinct()
        )).scalars().all())

    async def paged_ids(
        self,
        user_id: uuid.UUID,
        signals: list[str],
        limit: int,
        offset: int,
    ) -> tuple[list[int], int]:
        total = (await self._s.execute(
            select(func.count(func.distinct(Feedback.opportunity_id)))
            .where(Feedback.user_id == user_id, Feedback.signal.in_(signals))
        )).scalar_one()
        rows = (await self._s.execute(
            select(
                Feedback.opportunity_id,
                func.max(Feedback.created_at).label("ts"),
            )
            .where(Feedback.user_id == user_id, Feedback.signal.in_(signals))
            .group_by(Feedback.opportunity_id)
            .order_by(func.max(Feedback.created_at).desc())
            .limit(limit).offset(offset)
        )).all()
        return [r.opportunity_id for r in rows], int(total)