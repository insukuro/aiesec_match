import uuid

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.consent_service import ConsentService
from ..application.deps import current_user_id
from ..application.link_code_service import LinkCodeService
from ..application.me_service import MeService
from ..db import get_session
from ..schemas import ConsentIn, LinkCodeOut, MeOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
async def get_me(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await MeService(session).get_me(user_id)


@router.delete("", status_code=204)
async def delete_me(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    await MeService(session).delete_me(user_id)


@router.post("/consents", status_code=204)
async def add_consent(
    body: ConsentIn,
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    await ConsentService(session).add(user_id, body.kind, body.version)


@router.delete("/consents/{kind}", status_code=204)
async def revoke_consent(
    kind: str = Path(..., pattern="^(pd_processing|marketing)$"),
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    await ConsentService(session).revoke(user_id, kind)


@router.post("/link-codes", response_model=LinkCodeOut)
async def create_link_code(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await LinkCodeService(session).create_for_user(user_id)