import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.analytics_service import AnalyticsService
from ..application.deps import current_user_id
from ..db import get_session
from ..schemas import AnalyticsOut

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/me", response_model=AnalyticsOut)
async def analytics_me(
    period: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    from_: str | None = Query(None, alias="from"),
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await AnalyticsService(session).me(user_id, period, from_)