from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.age import age_from_birth
from ..domain.completeness import completeness
from ..errors import ProfileNotFound, Validation, VersionConflict
from ..infrastructure.repositories.profile_repo import ProfileRepo
from ..schemas import ProfileIn, ProfileOut, ProfileVersionEntry, ProfileVersionSnapshot


class ProfileService:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._profiles = ProfileRepo(session)

    async def get_current(self, user_id) -> ProfileOut:
        p = await self._profiles.get(user_id)
        if p is None:
            raise ProfileNotFound()
        v = await self._profiles.get_version(user_id, p.current_version)
        return ProfileOut(
            **v.body,
            profile_version=p.current_version,
            age_years=age_from_birth(v.birth_date),
            completeness=float(v.completeness),
            updated_at=p.updated_at,
        )

    async def put(
        self,
        user_id,
        body: ProfileIn,
        if_match: str | None,
    ) -> ProfileOut:
        # consent НЕ требуется — consent запрашивается отдельно и проверяется при matching
        if body.birth_date is not None:
            age = age_from_birth(body.birth_date)
            if age is None or age < 18 or age > 31:
                code = "birth_date_too_young" if (age or 0) < 18 else "birth_date_too_old"
                from ..domain.age import AGE_ERROR_MESSAGES
                raise Validation(errors=[{
                    "loc": ["body", "birth_date"],
                    "msg": AGE_ERROR_MESSAGES.get(code, "Недопустимый возраст"),
                }])

        p = await self._profiles.get_for_update(user_id)
        if p is None:
            p = await self._profiles.create_empty(user_id)

        if if_match and if_match.strip('"') != str(p.current_version):
            raise VersionConflict()

        new_version = p.current_version + 1
        data = body.model_dump(exclude_none=False, mode="json")
        c = completeness(data)
        await self._profiles.add_version(
            user_id, new_version, data, body.birth_date, c,
        )
        await self._profiles.set_current_version(p, new_version)
        await self._s.commit()

        return ProfileOut(
            **data,
            profile_version=new_version,
            age_years=age_from_birth(body.birth_date),
            completeness=c,
            updated_at=p.updated_at,
        )

    async def list_versions(self, user_id) -> list[ProfileVersionEntry]:
        rows = await self._profiles.list_versions(user_id)
        return [
            ProfileVersionEntry(
                version=r.version, created_at=r.created_at, completeness=float(r.completeness),
            )
            for r in rows
        ]

    async def get_version(self, user_id, version: int) -> ProfileVersionSnapshot:
        v = await self._profiles.get_version(user_id, version)
        if v is None:
            raise ProfileNotFound()
        return ProfileVersionSnapshot(
            **v.body,
            version=v.version,
            created_at=v.created_at,
            profile_version=v.version,
            age_years=age_from_birth(v.birth_date),
            completeness=float(v.completeness),
            updated_at=v.created_at,
        )