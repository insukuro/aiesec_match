from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Subscription


class SubscriptionRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def get(self, user_id: uuid.UUID) -> Subscription | None:
        return await self._s.get(Subscription, user_id)

    async def get_for_update(self, user_id: uuid.UUID) -> Subscription | None:
        return (await self._s.execute(
            select(Subscription).where(Subscription.user_id == user_id).with_for_update()
        )).scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        notify_new_matches: bool,
        min_score: float,
        channels: list[str],
    ) -> Subscription:
        s = await self.get_for_update(user_id)
        if s is None:
            s = Subscription(user_id=user_id)
            self._s.add(s)
        s.notify_new_matches = notify_new_matches
        s.min_score = Decimal(str(min_score))
        s.channels = channels
        s.updated_at = datetime.now(timezone.utc)
        return s