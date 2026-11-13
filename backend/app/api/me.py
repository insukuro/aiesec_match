from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_user
from ..db import get_session
from ..models import Consent, DeviceSecret, Identity, LinkCode, PasswordCredential, Profile, User
from ..schemas import ConsentIn, MeOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
async def get_me(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    profile = await session.get(Profile, user.user_id)
    idents = (await session.execute(select(Identity).where(Identity.user_id == user.user_id))).scalars().all()
    consents = (await session.execute(select(Consent).where(Consent.user_id == user.user_id))).scalars().all()
    email: str | None = None
    if not user.is_anonymous:
        cred = await session.get(PasswordCredential, user.user_id)
        if cred is not None:
            email = cred.email
    return MeOut(
        user_id=str(user.user_id),
        is_anonymous=user.is_anonymous,
        email=email,
        has_profile=profile is not None,
        profile_version=profile.current_version if profile else None,
        identities=[{"provider": i.provider, "external_id": i.external_id} for i in idents],
        consents=[{"kind": c.kind, "version": c.version, "accepted_at": c.accepted_at} for c in consents],
    )


@router.delete("", status_code=204)
async def delete_me(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    u = (await session.execute(
        select(User).where(User.user_id == user.user_id).with_for_update()
    )).scalar_one()
    u.deleted_at = datetime.now(timezone.utc)
    await session.execute(delete(DeviceSecret).where(DeviceSecret.user_id == u.user_id))
    await session.delete(u)
    await session.commit()


@router.post("/consents", status_code=204)
async def add_consent(body: ConsentIn, user: User = Depends(current_user),
                      session: AsyncSession = Depends(get_session)):
    existing = await session.get(Consent, (user.user_id, body.kind, body.version))
    if existing is None:
        session.add(Consent(user_id=user.user_id, kind=body.kind, version=body.version))
        await session.commit()


@router.post("/link-codes")
async def create_link_code(user: User = Depends(current_user),
                           session: AsyncSession = Depends(get_session)):
    import secrets
    code = secrets.token_urlsafe(6)[:8].upper()
    exp = datetime.now(timezone.utc) + timedelta(minutes=10)
    session.add(LinkCode(code=code, user_id=user.user_id, expires_at=exp))
    await session.commit()
    return {"code": code, "expires_in": 600}