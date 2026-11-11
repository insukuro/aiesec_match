from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_user
from ..db import get_session
from ..models import Subscription, User
from ..schemas import SubscriptionPrefs

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=SubscriptionPrefs)
async def get_(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    s = await session.get(Subscription, user.user_id)
    if s is None:
        return SubscriptionPrefs()
    return SubscriptionPrefs(notify_new_matches=s.notify_new_matches,
                             min_score=float(s.min_score), channels=s.channels)


@router.put("/me", response_model=SubscriptionPrefs)
async def put_(body: SubscriptionPrefs, user: User = Depends(current_user),
               session: AsyncSession = Depends(get_session)):
    s = (await session.execute(
        select(Subscription).where(Subscription.user_id == user.user_id).with_for_update()
    )).scalar_one_or_none()
    if s is None:
        s = Subscription(user_id=user.user_id)
        session.add(s)
    s.notify_new_matches = body.notify_new_matches
    s.min_score = body.min_score
    s.channels = body.channels
    s.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return body