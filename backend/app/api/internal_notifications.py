import hmac
import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..application.link_code_service import LinkCodeService
from ..application.notification_service import NotificationService
from ..db import get_session
from ..errors import Unauthorized


async def require_internal_token(
    x_internal_token: str | None = Header(default=None),
) -> None:
    expected = get_settings().internal_token
    if (
        not expected
        or x_internal_token is None
        or not hmac.compare_digest(x_internal_token, expected)
    ):
        raise Unauthorized()


router = APIRouter(
    tags=["internal"],
    dependencies=[Depends(require_internal_token)],
)


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