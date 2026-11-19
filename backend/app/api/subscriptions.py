import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.deps import current_user_id
from ..application.subscription_service import SubscriptionService
from ..db import get_session
from ..schemas import SubscriptionPrefs

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=SubscriptionPrefs)
async def get_(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await SubscriptionService(session).get(user_id)


@router.put("/me", response_model=SubscriptionPrefs)
async def put_(
    body: SubscriptionPrefs,
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await SubscriptionService(session).put(user_id, body)