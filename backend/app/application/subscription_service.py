from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.repositories.subscription_repo import SubscriptionRepo
from ..schemas import SubscriptionPrefs


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._repo = SubscriptionRepo(session)

    async def get(self, user_id) -> SubscriptionPrefs:
        s = await self._repo.get(user_id)
        if s is None:
            return SubscriptionPrefs()
        return SubscriptionPrefs(
            notify_new_matches=s.notify_new_matches,
            min_score=float(s.min_score),
            channels=s.channels,
        )

    async def put(self, user_id, body: SubscriptionPrefs) -> SubscriptionPrefs:
        await self._repo.upsert(
            user_id, body.notify_new_matches, body.min_score, body.channels,
        )
        await self._s.commit()
        return body