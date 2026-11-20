import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.auth_service import AuthService
from ..application.deps import current_user_id
from ..config import get_settings
from ..db import get_session
from ..errors import EmailDeliveryUnavailable
from ..schemas import (
    ChangeEmailIn, ChangePasswordIn, LoginIn, RegisterIn, TelegramAuthIn,
    TokenOut, VerifyEmailIn,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
async def register(body: RegisterIn, session: AsyncSession = Depends(get_session)):
    token, ttl = await AuthService(session).register(body.email, body.password)
    return TokenOut(access_token=token, expires_in=ttl)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, session: AsyncSession = Depends(get_session)):
    token, ttl = await AuthService(session).login(body.email, body.password)
    return TokenOut(access_token=token, expires_in=ttl)


@router.post("/telegram", response_model=TokenOut)
async def telegram_auth(body: TelegramAuthIn, session: AsyncSession = Depends(get_session)):
    token, ttl = await AuthService(session).telegram(body.init_data)
    return TokenOut(access_token=token, expires_in=ttl)


@router.post("/change-password", status_code=204)
async def change_password(
    body: ChangePasswordIn,
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    await AuthService(session).change_password(
        user_id, body.current_password, body.new_password,
    )


@router.post("/change-email")
async def request_email_change(
    body: ChangeEmailIn,
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    if not get_settings().dev_mode:
        raise EmailDeliveryUnavailable(
            "Email change requires an email delivery provider.",
        )
    code = await AuthService(session).request_email_change(
        user_id, body.new_email, body.password,
    )
    return {"status": "verification_required", "dev_code": code}


@router.post("/verify-email", status_code=204)
async def verify_email_change(
    new_email: str,
    body: VerifyEmailIn,
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    await AuthService(session).verify_email_change(user_id, new_email, body.code)