import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.link_code_service import LinkCodeService
from ..application.notification_service import NotificationService
from ..db import get_session
from ..schemas import LinkCodeConfirmIn

router = APIRouter(tags=["internal"])


@router.post("/notifications/lease")
async def lease(
    limit: int = 50,
    lease_seconds: int = 120,
    session: AsyncSession = Depends(get_session),
):
    return await NotificationService(session).lease(limit, lease_seconds)


@router.post("/notifications/{notification_id}/ack", status_code=204)
async def ack(
    notification_id: uuid.UUID,
    body: dict,
    session: AsyncSession = Depends(get_session),
):
    await NotificationService(session).ack(notification_id, body.get("error"))


@router.post("/link-codes/consume")
async def consume_link_code(
    code: str,
    telegram_chat_id: int,
    telegram_external_id: str,
    session: AsyncSession = Depends(get_session),
):
    user_id = await LinkCodeService(session).consume(
        code, telegram_chat_id, telegram_external_id,
    )
    return {"user_id": str(user_id)}