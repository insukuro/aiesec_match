from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import ProfileNotFound
from ..infrastructure.repositories.consent_repo import ConsentRepo
from ..infrastructure.repositories.profile_repo import ProfileRepo
from ..infrastructure.repositories.user_repo import UserRepo
from ..schemas import MeOut


class MeService:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._users = UserRepo(session)
        self._profiles = ProfileRepo(session)
        self._consents = ConsentRepo(session)

    async def get_me(self, user_id) -> MeOut:
        user = await self._users.get(user_id)
        if user is None:
            raise ProfileNotFound()
        profile = await self._profiles.get(user_id)
        idents = await self._users.identities_for(user_id)
        consents = await self._consents.list_for(user_id)
        cred = await self._users.get_credential(user_id)
        email = cred.email if cred else None
        email_verified = bool(cred and cred.email_verified_at)
        return MeOut(
            user_id=str(user.user_id),
            email=email,
            email_verified=email_verified,
            has_profile=profile is not None,
            profile_version=profile.current_version if profile else None,
            identities=[{"provider": i.provider, "external_id": i.external_id} for i in idents],
            consents=[
                {"kind": c.kind, "version": c.version, "accepted_at": c.accepted_at}
                for c in consents
            ],
        )

    async def delete_me(self, user_id) -> None:
        user = await self._users.get(user_id)
        if user is None:
            return
        await self._users.soft_delete(user)
        await self._s.commit()