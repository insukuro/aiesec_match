from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import NotificationNotFound
from ..infrastructure.repositories.outbox_repo import OutboxRepo
from ..schemas import NotificationItem, NotificationsPage


class NotificationService:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._repo = OutboxRepo(session)

    # ---------- consumer (bot) ----------

    async def lease(self, limit: int, lease_seconds: int) -> list[dict]:
        rows = await self._repo.lease(limit, lease_seconds)
        await self._s.commit()
        return [
            {
                "notification_id": str(r.notification_id),
                "telegram_chat_id": r.telegram_chat_id,
                "kind": r.kind,
                "created_at": r.created_at,
                "items": (r.payload or {}).get("items", []),
            }
            for r in rows
        ]

    async def ack(self, notification_id: uuid.UUID, error: str | None) -> None:
        await self._repo.ack(notification_id, error)
        await self._s.commit()

    # ---------- in-app ----------

    async def list_for_user(
        self, user_id: uuid.UUID, limit: int, offset: int,
    ) -> NotificationsPage:
        rows, total, unread = await self._repo.list_for_user(user_id, limit, offset)
        items = [
            NotificationItem(
                notification_id=str(r.notification_id),
                kind=r.kind,
                payload=r.payload or {},
                created_at=r.created_at,
                sent_at=r.sent_at,
                read_at=r.read_at,
            )
            for r in rows
        ]
        return NotificationsPage(
            items=items, total=total, limit=limit, offset=offset, unread=unread,
        )

    async def mark_read(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
        n = await self._repo.get_for_user(user_id, notification_id)
        if n is None:
            raise NotificationNotFound()
        if n.read_at is None:
            await self._repo.mark_read(user_id, notification_id)
            await self._s.commit()