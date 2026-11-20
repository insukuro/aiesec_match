from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import (
    IdentityConflict, InvalidLinkCode, LinkCodeAlreadyUsed, LinkCodeExpired,
)
from ..infrastructure.repositories.link_code_repo import LinkCodeRepo
from ..infrastructure.repositories.outbox_repo import OutboxRepo
from ..infrastructure.repositories.user_repo import UserRepo


class LinkCodeService:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._codes = LinkCodeRepo(session)
        self._users = UserRepo(session)
        self._outbox = OutboxRepo(session)

    async def create_for_user(self, user_id: uuid.UUID) -> dict:
        code = secrets.token_urlsafe(6)[:8].upper()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        await self._codes.create(code, user_id, expires_at)
        await self._s.commit()
        return {"code": code, "expires_in": 600}

    async def consume(
        self, code: str, telegram_chat_id: int, telegram_external_id: str,
    ) -> uuid.UUID:
        """Вызывается ботом (consumer) после /start <code>."""
        lc = await self._codes.get(code.upper())
        if lc is None:
            raise InvalidLinkCode()
        now = datetime.now(timezone.utc)
        if lc.used_at is not None:
            raise LinkCodeAlreadyUsed()
        if lc.expires_at < now:
            raise LinkCodeExpired()

        # Telegram уже привязан к другому пользователю?
        existing = await self._users.get_identity("telegram", telegram_external_id)
        if existing is not None and existing.user_id != lc.user_id:
            raise IdentityConflict()

        if existing is None:
            await self._users.add_identity(
                lc.user_id, "telegram", telegram_external_id,
            )
        await self._codes.mark_used(lc)
        await self._outbox.update_chat_id_for_user(lc.user_id, telegram_chat_id)
        await self._s.commit()
        return lc.user_id
