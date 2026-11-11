from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import NotificationOutbox

router = APIRouter(prefix="/notifications", tags=["internal"])


@router.post("/lease")
async def lease(limit: int = 50, lease_seconds: int = 120,
                session: AsyncSession = Depends(get_session)):
    now = datetime.now(timezone.utc)
    until = now + timedelta(seconds=lease_seconds)
    rows = (await session.execute(text("""
        WITH picked AS (
            SELECT notification_id FROM core.notification_outbox
            WHERE state IN ('pending','retry')
              AND (locked_until IS NULL OR locked_until < :now)
            ORDER BY created_at
            LIMIT :lim
            FOR UPDATE SKIP LOCKED
        )
        UPDATE core.notification_outbox o
        SET locked_until = :until, attempts = o.attempts + 1, state = 'leased'
        FROM picked WHERE o.notification_id = picked.notification_id
        RETURNING o.notification_id, o.telegram_chat_id, o.kind, o.created_at, o.payload
    """), {"now": now, "until": until, "lim": min(limit, 50)})).mappings().all()
    await session.commit()
    return [{"notification_id": str(r["notification_id"]), "telegram_chat_id": r["telegram_chat_id"],
             "kind": r["kind"], "created_at": r["created_at"], "items": r["payload"].get("items", [])}
            for r in rows]


@router.post("/{notification_id}/ack", status_code=204)
async def ack(notification_id: str, body: dict, session: AsyncSession = Depends(get_session)):
    if body.get("error") == "blocked":
        await session.execute(text("""
            UPDATE core.subscriptions s SET notify_new_matches = false
            FROM core.notification_outbox o
            WHERE o.notification_id = :n AND s.user_id = o.user_id
        """), {"n": notification_id})
    await session.execute(text("""
        UPDATE core.notification_outbox
        SET state = CASE WHEN :err IS NULL THEN 'sent' ELSE 'failed' END,
            sent_at = CASE WHEN :err IS NULL THEN now() ELSE sent_at END,
            locked_until = NULL
        WHERE notification_id = :n
    """), {"n": notification_id, "err": body.get("error")})
    await session.commit()