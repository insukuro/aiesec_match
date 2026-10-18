from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..client import AiesecError, AuthError, NotSupported

from ..models import Opportunity
from ..runtime import service, targets
from .deps import get_db

router = APIRouter()

LIST_EXCLUDE = {"raw"}


def to_dict(row: Opportunity, full: bool = False) -> dict:
    return {
        c.name: getattr(row, c.name)
        for c in Opportunity.__table__.columns
        if full or c.name not in LIST_EXCLUDE
    }


def _actual_clause():
    return (Opportunity.is_open.is_(True)) & (
        Opportunity.applications_close_date.is_(None)
        | (Opportunity.applications_close_date >= date.today())
    )


@router.get("/opportunities", tags=["opportunities"])
def list_opportunities(
    country: str | None = Query(None, description="Название страны из targets.json"),
    city: str | None = Query(None, description="Город Турции из targets.json"),
    home_mc_id: int | None = None,
    home_lc_id: int | None = None,
    programme_id: int | None = None,
    q: str | None = Query(None, description="Поиск по названию"),
    only_open: bool = True,
    closing_before: date | None = None,
    new_since: datetime | None = Query(None, description="Впервые увидели после (UTC)"),
    updated_since: datetime | None = Query(
        None,
        description="Изменились/закрылись после (UTC). Используйте с only_open=false",
    ),
    sort: Literal["first_seen_at", "applications_close_date", "date_opened", "updated_at",
                  "remote_updated_at"] = "first_seen_at",
    desc: bool = True,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    conds = []
    if only_open:
        conds.append(_actual_clause())
    if country:
        mc = next((v for k, v in targets.countries.items() if k.lower() == country.lower()), None)
        if mc is None:
            raise HTTPException(404, f"Страна '{country}' не в targets.json")
        conds.append(Opportunity.home_mc_id == mc)
    if city:
        lc = next((v for k, v in targets.turkey_cities.items() if k.lower() == city.lower()), None)
        if lc is None:
            raise HTTPException(404, f"Город '{city}' не в targets.json")
        conds.append(or_(Opportunity.home_lc_id == lc, Opportunity.host_lc_id == lc))
    if home_mc_id is not None:
        conds.append(Opportunity.home_mc_id == home_mc_id)
    if home_lc_id is not None:
        conds.append(Opportunity.home_lc_id == home_lc_id)
    if programme_id is not None:
        conds.append(Opportunity.programme_id == programme_id)
    if q:
        conds.append(Opportunity.title.ilike(f"%{q}%"))
    if closing_before:
        conds.append(Opportunity.applications_close_date <= closing_before)
    if new_since:
        conds.append(Opportunity.first_seen_at >= new_since)
    if updated_since:
        conds.append(Opportunity.updated_at >= updated_since)

    col = getattr(Opportunity, sort)
    total = db.scalar(select(func.count()).select_from(Opportunity).where(*conds))
    rows = db.scalars(
        select(Opportunity).where(*conds)
        .order_by(col.desc() if desc else col.asc()).limit(limit).offset(offset)
    ).all()
    return {"total": total, "limit": limit, "offset": offset, "items": [to_dict(r) for r in rows]}


@router.get("/opportunities/stats", tags=["opportunities"])
def opportunities_stats(db: Session = Depends(get_db)):
    clause = _actual_clause()
    by_mc = dict(db.execute(
        select(Opportunity.home_mc_id, func.count()).where(clause)
        .group_by(Opportunity.home_mc_id)
    ).all())
    by_lc = dict(db.execute(
        select(Opportunity.home_lc_id, func.count()).where(clause)
        .group_by(Opportunity.home_lc_id)
    ).all())
    return {
        "open_total": db.scalar(select(func.count()).select_from(Opportunity).where(clause)),
        "countries": {n: by_mc.get(i, 0) for n, i in targets.countries.items()},
        "turkey_cities": {n: by_lc.get(i, 0) for n, i in targets.turkey_cities.items()},
        "last_full_at": service.get_state("last_full_at"),
        "last_incremental_at": service.get_state("last_incremental_at"),
        "last_reconcile_at": service.get_state("last_reconcile_at"),
    }


@router.get("/opportunities/{opportunity_id}", tags=["opportunities"])
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    row = db.get(Opportunity, opportunity_id)
    if not row:
        raise HTTPException(404, "Стажировка не найдена в базе")
    return to_dict(row, full=True)


@router.post("/opportunities/{opportunity_id}/refresh", tags=["opportunities"])
def refresh_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    try:
        result = service.refresh_one(opportunity_id)
    except NotSupported as e:
        raise HTTPException(501, str(e))
    except AuthError as e:
        raise HTTPException(502, f"AIESEC отклонил токен: {e}")
    except AiesecError as e:
        raise HTTPException(502, f"Ошибка AIESEC API: {e}")
    db.expire_all()
    row = db.get(Opportunity, opportunity_id)
    return {**result, "opportunity": to_dict(row) if row else None}