import uuid

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.deps import current_user_id, get_matcher
from ..application.matching_service import MatchingService
from ..db import get_session
from ..infrastructure.matcher_client import MatcherClient
from ..schemas import RecommendationRunIn

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("")
async def create_run(
    body: RecommendationRunIn,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8),
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
    matcher: MatcherClient = Depends(get_matcher),
    response: Response = None,
):
    result = await MatchingService(session, matcher).create_run(
        user_id, body, idempotency_key,
    )
    if response is not None:
        response.status_code = 202 if body.mode == "async" else 200
    return result


@router.get("")
async def list_runs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
    matcher: MatcherClient = Depends(get_matcher),
):
    return await MatchingService(session, matcher).list_runs(user_id, limit, offset)


@router.get("/latest")
async def latest(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
    matcher: MatcherClient = Depends(get_matcher),
):
    return await MatchingService(session, matcher).latest(user_id)


@router.get("/{run_id}")
async def get_run(
    run_id: uuid.UUID,
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
    matcher: MatcherClient = Depends(get_matcher),
):
    return await MatchingService(session, matcher).get_run(user_id, run_id)