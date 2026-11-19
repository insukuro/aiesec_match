import uuid

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.deps import current_user_id
from ..application.profile_service import ProfileService
from ..db import get_session
from ..schemas import ProfileIn, ProfileOut, ProfileVersionEntry, ProfileVersionSnapshot

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileOut)
async def get_me(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
    response: Response = None,
):
    out = await ProfileService(session).get_current(user_id)
    if response is not None:
        response.headers["ETag"] = f'"{out.profile_version}"'
    return out


@router.put("/me", response_model=ProfileOut)
async def put_me(
    body: ProfileIn,
    if_match: str | None = Header(default=None, alias="If-Match"),
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
    response: Response = None,
):
    out = await ProfileService(session).put(user_id, body, if_match)
    if response is not None:
        response.headers["ETag"] = f'"{out.profile_version}"'
    return out


@router.get("/me/versions", response_model=list[ProfileVersionEntry])
async def list_versions(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await ProfileService(session).list_versions(user_id)


@router.get("/me/versions/{version}", response_model=ProfileVersionSnapshot)
async def get_version(
    version: int,
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await ProfileService(session).get_version(user_id, version)