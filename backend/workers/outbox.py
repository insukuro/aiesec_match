"""Сборка уведомлений в outbox для подписчиков.

Отправку в Telegram выполняет внешний consumer через
/internal/v1/notifications/*. Здесь только payload и dedupe.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.outbox_repo import OutboxRepo
from app.infrastructure.repositories.subscription_repo import SubscriptionRepo


async def enqueue_for_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    run_id: str,
    items: list[dict],
) -> None:
    sub = await SubscriptionRepo(session).get(user_id)
    if sub is None or not sub.notify_new_matches:
        return
    dedupe = f"{user_id}:{run_id}"
    outbox = OutboxRepo(session)
    if await outbox.has_dedupe(dedupe):
        return
    await outbox.add(
        user_id=user_id,
        kind="new_matches",
        payload={"run_id": run_id, "items": items[:3]},
        dedupe_key=dedupe,
    )