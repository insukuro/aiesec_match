from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_user
from ..completeness import completeness
from ..db import get_session
from ..errors import ConsentRequired, ProfileNotFound, VersionConflict
from ..models import Consent, Profile, ProfileVersion, User
from ..schemas import ProfileIn, ProfileOut

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _age(birth):
    if not birth: return None
    today = datetime.now(timezone.utc).date()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


@router.get("/me", response_model=ProfileOut)
async def get_me(user: User = Depends(current_user), session: AsyncSession = Depends(get_session),
                 response: Response = None):
    p = await session.get(Profile, user.user_id)
    if p is None:
        raise ProfileNotFound()
    v = await session.get(ProfileVersion, (user.user_id, p.current_version))
    out = ProfileOut(**v.body, profile_version=p.current_version, age_years=_age(v.birth_date),
                     completeness=float(v.completeness), updated_at=p.updated_at)
    if response is not None:
        response.headers["ETag"] = f'"{p.current_version}"'
    return out


@router.put("/me", response_model=ProfileOut)
async def put_me(body: ProfileIn, if_match: str | None = Header(default=None, alias="If-Match"),
                 user: User = Depends(current_user), session: AsyncSession = Depends(get_session),
                 response: Response = None):
    consent = (await session.execute(
        select(Consent).where(Consent.user_id == user.user_id, Consent.kind == "pd_processing")
    )).scalar_one_or_none()
    if consent is None:
        raise ConsentRequired()

    # SELECT FOR UPDATE profiles (или создать)
    p = (await session.execute(
        select(Profile).where(Profile.user_id == user.user_id).with_for_update()
    )).scalar_one_or_none()
    if p is None:
        p = Profile(user_id=user.user_id, current_version=0, updated_at=datetime.now(timezone.utc))
        session.add(p)
        await session.flush()

    if if_match and if_match.strip('"') != str(p.current_version):
        raise VersionConflict()

    new_version = p.current_version + 1
    data = body.model_dump(exclude_none=False)
    c = completeness(data)
    session.add(ProfileVersion(user_id=user.user_id, version=new_version, body=data,
                               birth_date=body.birth_date, completeness=c))
    p.current_version = new_version
    p.updated_at = datetime.now(timezone.utc)
    await session.commit()

    out = ProfileOut(**data, profile_version=new_version, age_years=_age(body.birth_date),
                     completeness=c, updated_at=p.updated_at)
    if response is not None:
        response.headers["ETag"] = f'"{new_version}"'
    return out