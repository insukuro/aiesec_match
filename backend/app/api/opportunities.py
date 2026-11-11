from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..catalog import fetch_cards, fetch_requirements, list_opportunities
from ..db import get_session
from ..errors import OpportunityNotFound
from ..schemas import Page
from .recommendations import _card

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=Page)
async def list_(
    q: str | None = None, programme_kind: str | None = None, country_code: str | None = None,
    lc_id: int | None = None, family_key: str | None = None, only_open: bool = True,
    sort: str = Query("new", pattern="^(new|closing|chance)$"),
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    rows, total = await list_opportunities(
        session, q=q, programme_kind=programme_kind, country_code=country_code,
        lc_id=lc_id, family_key=family_key, only_open=only_open,
        sort=sort, limit=limit, offset=offset,
    )
    ids = [r["opportunity_id"] for r in rows]
    reqs = await fetch_requirements(session, ids)
    return Page(items=[_card(r, reqs.get(r["opportunity_id"], [])) for r in rows],
                total=total, limit=limit, offset=offset)


@router.get("/{opportunity_id}")
async def detail(opportunity_id: int, session: AsyncSession = Depends(get_session)):
    cards = await fetch_cards(session, [opportunity_id])
    if not cards:
        raise OpportunityNotFound()
    reqs = await fetch_requirements(session, [opportunity_id])
    c = _card(cards[opportunity_id], reqs.get(opportunity_id, []))
    c.update({
        "earliest_start_date": cards[opportunity_id]["earliest_start_date"],
        "latest_end_date": cards[opportunity_id]["latest_end_date"],
        "experience_type": cards[opportunity_id]["experience_type"],
        "close_reason": cards[opportunity_id]["close_reason"],
        "family": {"family_key": c["family_key"], "siblings_count": 0},
    })
    return c