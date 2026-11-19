from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.catalog_service import CatalogService
from ..db import get_session
from ..schemas import Page

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=Page)
async def list_(
    q: str | None = None,
    programme_kind: str | None = None,
    country_code: str | None = None,
    lc_id: int | None = None,
    family_key: str | None = None,
    only_open: bool = True,
    sort: str = Query("new", pattern="^(new|closing|chance)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    return await CatalogService(session).list(
        q=q, programme_kind=programme_kind, country_code=country_code,
        lc_id=lc_id, family_key=family_key, only_open=only_open,
        sort=sort, limit=limit, offset=offset,
    )


@router.get("/{opportunity_id}")
async def detail(opportunity_id: int, session: AsyncSession = Depends(get_session)):
    return await CatalogService(session).detail(opportunity_id)