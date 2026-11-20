from __future__ import annotations

import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..errors import Unauthorized
from ..infrastructure.matcher_client import MatcherClient
from ..infrastructure.repositories.user_repo import UserRepo
from .auth_service import decode_token

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


async def current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> uuid.UUID:
    if creds is None:
        raise Unauthorized()
    user_id = decode_token(creds.credentials)
    if await UserRepo(session).get(user_id) is None:
        raise Unauthorized()
    return user_id


async def get_matcher(request: Request) -> MatcherClient:
    return request.app.state.matcher


def session_dep() -> AsyncSession:
    return Depends(get_session)