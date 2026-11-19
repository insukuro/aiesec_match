import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.deps import current_user_id
from ..application.history_service import HistoryService
from ..db import get_session

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
async def history(
    type: str | None = Query(None),
    frm: str | None = Query(None, alias="from"),
    to: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await HistoryService(session).list(
        user_id, type=type, frm=frm, to=to, limit=limit, offset=offset,
    )