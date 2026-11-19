from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Profile, ProfileVersion


class ProfileRepo:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def get(self, user_id: uuid.UUID) -> Profile | None:
        return await self._s.get(Profile, user_id)

    async def get_for_update(self, user_id: uuid.UUID) -> Profile | None:
        return (await self._s.execute(
            select(Profile).where(Profile.user_id == user_id).with_for_update()
        )).scalar_one_or_none()

    async def get_version(self, user_id: uuid.UUID, version: int) -> ProfileVersion | None:
        return await self._s.get(ProfileVersion, (user_id, version))

    async def list_versions(self, user_id: uuid.UUID) -> list[ProfileVersion]:
        return list((await self._s.execute(
            select(ProfileVersion)
            .where(ProfileVersion.user_id == user_id)
            .order_by(ProfileVersion.version.desc())
        )).scalars().all())

    async def create_empty(self, user_id: uuid.UUID) -> Profile:
        p = Profile(user_id=user_id, current_version=0, updated_at=datetime.now(timezone.utc))
        self._s.add(p)
        await self._s.flush()
        return p

    async def add_version(
        self,
        user_id: uuid.UUID,
        version: int,
        body: dict[str, Any],
        birth_date,
        completeness_value: float,
    ) -> None:
        self._s.add(ProfileVersion(
            user_id=user_id, version=version, body=body,
            birth_date=birth_date, completeness=Decimal(str(completeness_value)),
        ))

    async def set_current_version(
        self, profile: Profile, version: int,
    ) -> None:
        profile.current_version = version
        profile.updated_at = datetime.now(timezone.utc)