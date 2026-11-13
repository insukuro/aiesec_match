import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_user
from ..catalog import fetch_cards, fetch_requirements
from ..db import get_session
from ..models import User
from ..schemas import FeedbackIn

router = APIRouter(prefix="/feedback", tags=["feedback"])

VALID_SIGNALS = {"opened", "liked", "disliked", "hidden", "applied"}


@router.post("", status_code=204)
async def create(
    body: FeedbackIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if body.signal not in VALID_SIGNALS:
        raise HTTPException(422, detail={"type": "validation", "errors": [
            {"loc": ["body", "signal"], "msg": "invalid signal"}
        ]})
    run_id = uuid.UUID(body.run_id) if body.run_id else None
    await session.execute(
        text("""
            INSERT INTO core.feedback
                (feedback_id, user_id, run_id, opportunity_id, signal, created_at)
            VALUES
                (:id, :u, :r, :o, :s, :now)
            ON CONFLICT (user_id, opportunity_id, signal) DO NOTHING
        """),
        {
            "id": uuid.uuid4(),
            "u": user.user_id,
            "r": run_id,
            "o": body.opportunity_id,
            "s": body.signal,
            "now": datetime.now(timezone.utc),
        },
    )
    await session.commit()


@router.delete("/{opportunity_id}", status_code=204)
async def delete_signal(
    opportunity_id: int,
    signal: str = Query(..., pattern="^(liked|disliked|hidden|opened|applied)$"),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    await session.execute(
        text("""
            DELETE FROM core.feedback
            WHERE user_id = :u AND opportunity_id = :o AND signal = :s
        """),
        {"u": user.user_id, "o": opportunity_id, "s": signal},
    )
    await session.commit()


@router.get("/liked")
async def liked(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await _list_by_signal(session, user.user_id, {"liked"}, limit, offset)


@router.get("/hidden")
async def hidden(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await _list_by_signal(session, user.user_id, {"hidden", "disliked"}, limit, offset)


async def _list_by_signal(
    session: AsyncSession,
    user_id: uuid.UUID,
    signals: set[str],
    limit: int,
    offset: int,
) -> dict:
    signal_list = list(signals)
    total = (await session.execute(
        text("""
            SELECT COUNT(DISTINCT opportunity_id) FROM core.feedback
            WHERE user_id = :u AND signal = ANY(:signals)
        """),
        {"u": user_id, "signals": signal_list},
    )).scalar_one()

    ids = (await session.execute(
        text("""
            SELECT opportunity_id, MAX(created_at) AS ts
            FROM core.feedback
            WHERE user_id = :u AND signal = ANY(:signals)
            GROUP BY opportunity_id
            ORDER BY ts DESC
            LIMIT :limit OFFSET :offset
        """),
        {"u": user_id, "signals": signal_list, "limit": limit, "offset": offset},
    )).all()

    opp_ids = [r.opportunity_id for r in ids]
    cards = await fetch_cards(session, opp_ids)
    reqs = await fetch_requirements(session, opp_ids)

    items = []
    for oid in opp_ids:
        c = cards.get(oid)
        if c is None:
            continue
        items.append({
            "opportunity_id": c["opportunity_id"],
            "title": c["title"],
            "family_key": c["family_key"],
            "programme": {
                "id": c["programme_id"],
                "kind": c["programme_kind"],
                "name": c.get("programme_kind") or c["programme_kind"],
            },
            "place": {
                "country_code": c["country_code"],
                "country_name": c["country_name"],
                "lc_id": c["lc_id"],
                "lc_name": c["lc_name"],
                "location": c["location"],
            },
            "organisation_name": c["organisation_name"],
            "capacity": {
                "openings": c["openings"],
                "available_openings": c["available_openings"],
                "applicants_count": c["applicants_count"],
                "accepted_count": c["accepted_count"],
            },
            "duration_weeks": c["duration_weeks"],
            "cost": ({"amount": float(c["cost_total"]), "currency": c["cost_currency"]}
                     if c["cost_total"] is not None else None),
            "requirements": [
                {"kind": r["kind"], "constant_id": r["constant_id"], "name": r["constant_name"],
                 "parent_name": r["parent_name"], "option": r["option"]}
                for r in reqs.get(oid, [])
            ],
            "date_opened": c["date_opened"],
            "applications_close_date": c["applications_close_date"],
            "is_open": c["is_open"],
            "updated_at": c["updated_at"],
        })

    return {"items": items, "total": int(total), "limit": limit, "offset": offset}