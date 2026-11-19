import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.deps import current_user_id
from ..application.feedback_service import FeedbackService
from ..db import get_session
from ..schemas import FeedbackIn

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=204)
async def create(
    body: FeedbackIn,
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    await FeedbackService(session).create(user_id, body)


@router.delete("/{opportunity_id}", status_code=204)
async def delete_signal(
    opportunity_id: int,
    signal: str = Query(..., pattern="^(liked|disliked|hidden|opened|applied)$"),
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    await FeedbackService(session).remove(user_id, opportunity_id, signal)


@router.get("/liked")
async def liked(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await FeedbackService(session).list_liked(user_id, limit, offset)


@router.get("/hidden")
async def hidden(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await FeedbackService(session).list_hidden(user_id, limit, offset)