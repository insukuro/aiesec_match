from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import require_registered
from ..db import get_session
from ..models import User

router = APIRouter(prefix="/history", tags=["history"])


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("")
async def history(
    type: str | None = Query(None),
    frm: str | None = Query(None, alias="from"),
    to: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
):
    since = _parse_dt(frm)
    until = _parse_dt(to)

    params: dict[str, Any] = {"u": user.user_id, "limit": limit, "offset": offset}

    runs_where = "rr.user_id = :u AND rr.state = 'succeeded' AND rr.finished_at IS NOT NULL"
    fb_where = "f.user_id = :u"
    if since is not None:
        params["since"] = since
        runs_where += " AND rr.finished_at >= :since"
        fb_where += " AND f.created_at >= :since"
    if until is not None:
        params["until"] = until
        runs_where += " AND rr.finished_at <= :until"
        fb_where += " AND f.created_at <= :until"

    # type-фильтр: не тащим NULL в SQL — конструируем условие в Python
    include_runs = type is None or type == "run_finished"
    include_feedback = type is None or type.startswith("signal_")
    signal_filter = type[len("signal_"):] if (type and type.startswith("signal_")) else None

    parts: list[str] = []
    if include_runs:
        parts.append(f"""
            SELECT
                'run_finished'::text AS type,
                rr.finished_at AS occurred_at,
                'Подбор завершён'::text AS title,
                CONCAT('Найдено ', rr.total_candidates, ' кандидатов') AS description,
                rr.run_id::text AS related_entity_id
            FROM core.recommendation_runs rr
            WHERE {runs_where}
        """)
    if include_feedback:
        if signal_filter is not None:
            params["signal"] = signal_filter
            fb_where_sig = fb_where + " AND f.signal = :signal"
        else:
            fb_where_sig = fb_where
        parts.append(f"""
            SELECT
                ('signal_' || f.signal)::text AS type,
                f.created_at AS occurred_at,
                CASE f.signal
                    WHEN 'liked'    THEN 'Понравилось'
                    WHEN 'disliked' THEN 'Не понравилось'
                    WHEN 'hidden'   THEN 'Скрыто'
                    WHEN 'applied'  THEN 'Отклик отправлен'
                    WHEN 'opened'   THEN 'Открыто'
                    ELSE f.signal END AS title,
                CONCAT('Вакансия #', f.opportunity_id) AS description,
                f.opportunity_id::text AS related_entity_id
            FROM core.feedback f
            WHERE {fb_where_sig}
        """)

    if not parts:
        # некорректный type — отдаём пустую страницу, а не 500
        return {"items": [], "total": 0, "limit": limit, "offset": offset}

    union_sql = " UNION ALL ".join(parts)

    rows = (await session.execute(text(f"""
        SELECT * FROM ({union_sql}) events
        ORDER BY occurred_at DESC
        LIMIT :limit OFFSET :offset
    """), params)).mappings().all()

    total = (await session.execute(text(f"""
        SELECT COUNT(*) FROM ({union_sql}) events
    """), params)).scalar_one()

    items = [
        {
            "event_id": f"{r['type']}:{r['related_entity_id']}:{r['occurred_at'].isoformat()}",
            "type": r["type"],
            "occurred_at": r["occurred_at"],
            "title": r["title"],
            "description": r["description"],
            "related_entity_id": r["related_entity_id"],
        }
        for r in rows
    ]
    return {"items": items, "total": int(total), "limit": limit, "offset": offset}