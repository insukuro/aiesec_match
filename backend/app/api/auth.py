from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    issue_token,
    login_with_password,
    register_with_password,
    resolve_or_create_anonymous,
    verify_telegram_init_data,
)
from ..config import get_settings
from ..db import get_session
from ..errors import BadCredentials, EmailTaken, Validation
from ..schemas import (
    AnonymousAuthIn,
    AnonymousAuthOut,
    LoginIn,
    RegisterIn,
    TelegramAuthIn,
    TokenOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/anonymous", response_model=AnonymousAuthOut)
async def anonymous(body: AnonymousAuthIn, session: AsyncSession = Depends(get_session)):
    user, new_secret = await resolve_or_create_anonymous(session, body.device_secret)
    token, ttl = issue_token(user.user_id, get_settings().jwt_ttl_seconds)
    return AnonymousAuthOut(access_token=token, expires_in=ttl, device_secret=new_secret)


@router.post("/register", response_model=TokenOut)
async def register(body: RegisterIn, session: AsyncSession = Depends(get_session)):
    try:
        user = await register_with_password(session, body.email, body.password)
    except ValueError as e:
        if str(e) == "email_taken":
            raise EmailTaken()
        raise
    token, ttl = issue_token(user.user_id, get_settings().jwt_ttl_seconds)
    return TokenOut(access_token=token, expires_in=ttl, is_anonymous=False)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, session: AsyncSession = Depends(get_session)):
    user = await login_with_password(session, body.email, body.password)
    if user is None:
        raise BadCredentials()
    token, ttl = issue_token(user.user_id, get_settings().jwt_ttl_seconds)
    return TokenOut(access_token=token, expires_in=ttl, is_anonymous=False)


@router.post("/telegram", response_model=TokenOut)
async def telegram_auth(body: TelegramAuthIn, session: AsyncSession = Depends(get_session)):
    user_info = verify_telegram_init_data(body.init_data, get_settings().telegram_bot_token)
    from ..models import Identity, User
    from sqlalchemy import select
    ext = str(user_info["id"])
    row = (await session.execute(
        select(Identity).where(Identity.provider == "telegram", Identity.external_id == ext)
    )).scalar_one_or_none()
    if row is None:
        user = User(is_anonymous=False)
        session.add(user)
        await session.flush()
        session.add(Identity(user_id=user.user_id, provider="telegram", external_id=ext))
        await session.commit()
    else:
        user = await session.get(User, row.user_id)
    token, ttl = issue_token(user.user_id, get_settings().jwt_ttl_seconds)
    return TokenOut(access_token=token, expires_in=ttl, is_anonymous=False)