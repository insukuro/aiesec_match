from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import NotificationOutbox, Subscription


class OutboxRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def has_dedupe(self, dedupe_key: str) -> bool:
        row = (await self._s.execute(
            select(NotificationOutbox).where(NotificationOutbox.dedupe_key == dedupe_key)
        )).scalar_one_or_none()
        return row is not None

    async def add(
        self,
        user_id: uuid.UUID,
        kind: str,
        payload: dict,
        dedupe_key: str,
    ) -> None:
        self._s.add(NotificationOutbox(
            user_id=user_id,
            kind=kind,
            payload=payload,
            state="pending",
            dedupe_key=dedupe_key,
        ))

    async def lease(self, limit: int, lease_seconds: int) -> list[NotificationOutbox]:
        now = datetime.now(timezone.utc)
        until = now + timedelta(seconds=lease_seconds)

        picked = (await self._s.execute(
            select(NotificationOutbox.notification_id)
            .where(
                NotificationOutbox.state.in_(("pending", "retry")),
                (NotificationOutbox.locked_until.is_(None))
                | (NotificationOutbox.locked_until < now),
            )
            .order_by(NotificationOutbox.created_at)
            .limit(min(limit, 50))
            .with_for_update(skip_locked=True)
        )).scalars().all()

        if not picked:
            return []

        await self._s.execute(
            update(NotificationOutbox)
            .where(NotificationOutbox.notification_id.in_(picked))
            .values(
                locked_until=until,
                attempts=NotificationOutbox.attempts + 1,
                state="leased",
            )
        )
        rows = (await self._s.execute(
            select(NotificationOutbox).where(
                NotificationOutbox.notification_id.in_(picked)
            )
        )).scalars().all()
        return list(rows)

    async def ack(self, notification_id: uuid.UUID, error: str | None) -> None:
        if error == "blocked":
            user_id = (await self._s.execute(
                select(NotificationOutbox.user_id).where(
                    NotificationOutbox.notification_id == notification_id
                )
            )).scalar_one_or_none()
            if user_id is not None:
                await self._s.execute(
                    update(Subscription)
                    .where(Subscription.user_id == user_id)
                    .values(notify_new_matches=False)
                )
        values: dict = {"locked_until": None}
        if error is None:
            values["state"] = "sent"
            values["sent_at"] = datetime.now(timezone.utc)
        else:
            values["state"] = "failed"
        await self._s.execute(
            update(NotificationOutbox)
            .where(NotificationOutbox.notification_id == notification_id)
            .values(**values)
        )

    # ---------- in-app notifications ----------

    async def list_for_user(
        self, user_id: uuid.UUID, limit: int, offset: int,
    ) -> tuple[list[NotificationOutbox], int, int]:
        total = (await self._s.execute(
            select(func.count()).select_from(NotificationOutbox).where(
                NotificationOutbox.user_id == user_id
            )
        )).scalar_one()
        unread = (await self._s.execute(
            select(func.count()).select_from(NotificationOutbox).where(
                NotificationOutbox.user_id == user_id,
                NotificationOutbox.read_at.is_(None),
            )
        )).scalar_one()
        rows = (await self._s.execute(
            select(NotificationOutbox)
            .where(NotificationOutbox.user_id == user_id)
            .order_by(NotificationOutbox.created_at.desc())
            .limit(limit).offset(offset)
        )).scalars().all()
        return list(rows), int(total), int(unread)

    async def get_for_user(
        self, user_id: uuid.UUID, notification_id: uuid.UUID,
    ) -> NotificationOutbox | None:
        return (await self._s.execute(
            select(NotificationOutbox).where(
                NotificationOutbox.notification_id == notification_id,
                NotificationOutbox.user_id == user_id,
            )
        )).scalar_one_or_none()

    async def mark_read(
        self, user_id: uuid.UUID, notification_id: uuid.UUID,
    ) -> bool:
        result = await self._s.execute(
            update(NotificationOutbox)
            .where(
                NotificationOutbox.notification_id == notification_id,
                NotificationOutbox.user_id == user_id,
                NotificationOutbox.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
        )
        return (result.rowcount or 0) > 0

    async def update_chat_id_for_user(
        self, user_id: uuid.UUID, chat_id: int,
    ) -> None:
        await self._s.execute(
            update(NotificationOutbox)
            .where(NotificationOutbox.user_id == user_id)
            .values(telegram_chat_id=chat_id)
        )