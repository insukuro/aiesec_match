"""Формирует уведомления в outbox для подписчиков.

Бот отсутствует; шаг «отправить в Telegram» выполняет внешний consumer
через /internal/v1/notifications/*. Здесь только сборка payload и dedupe.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..catalog import current_watermark
from ..models import NotificationOutbox, Profile, Subscription


async def enqueue_for_user(session: AsyncSession, user_id, run_id: str, items: list[dict]) -> None:
    sub = await session.get(Subscription, user_id)
    if sub is None or not sub.notify_new_matches:
        return
    dedupe = f"{user_id}:{run_id}"
    existing = (await session.execute(
        select(NotificationOutbox).where(NotificationOutbox.dedupe_key == dedupe)
    )).scalar_one_or_none()
    if existing:
        return
    session.add(NotificationOutbox(
        user_id=user_id, kind="new_matches", payload={"run_id": run_id, "items": items[:3]},
        state="pending", dedupe_key=dedupe,
    ))