from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import require_registered
from ..db import get_session
from ..models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])

PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90, "all": None}


def _since(period: str, frm: str | None) -> datetime | None:
    if frm:
        return datetime.fromisoformat(frm).replace(tzinfo=timezone.utc)
    days = PERIOD_DAYS.get(period)
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


@router.get("/me")
async def analytics_me(
    period: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None),
    user: User = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
):
    since = _since(period, from_)

    # 1. Заполненность профиля
    profile_row = (await session.execute(text("""
        SELECT p.current_version, v.body
        FROM core.profiles p
        LEFT JOIN core.profile_versions v
          ON v.user_id = p.user_id AND v.version = p.current_version
        WHERE p.user_id = :u
    """), {"u": user.user_id})).mappings().one_or_none()

    body: dict[str, Any] = dict(profile_row["body"]) if profile_row and profile_row["body"] else {}
    expected_keys = [
        "programmes", "english_level", "study", "work_experience",
        "spheres", "activities", "desired_countries", "duration",
        "start_window", "motivation_text", "financial",
    ]
    filled = sum(1 for k in expected_keys if body.get(k) not in (None, "", [], {}))
    total = len(expected_keys)
    percent = round(filled / total * 100) if total else 0

    # 2. Распределение по программам (из последнего успешного run)
    programme_rows = (await session.execute(text("""
        SELECT programme_kind, COUNT(*) AS cnt
        FROM core.recommendation_items ri
        JOIN core.recommendation_runs rr ON rr.run_id = ri.run_id
        WHERE rr.user_id = :u AND rr.state = 'succeeded'
          AND rr.run_id = (
              SELECT run_id FROM core.recommendation_runs
              WHERE user_id = :u AND state = 'succeeded'
              ORDER BY created_at DESC LIMIT 1
          )
        GROUP BY programme_kind
    """), {"u": user.user_id})).mappings().all()
    programme_distribution = [
        {"programme_kind": r["programme_kind"], "count": int(r["cnt"])} for r in programme_rows
    ]

    # 3. Интересы
    spheres = body.get("spheres") or []
    interests_distribution = [{"code": s, "label": s, "count": 1} for s in spheres]

    # 4. Активность по дням — условие на since добавляем только если оно есть.
    params: dict[str, Any] = {"u": user.user_id}
    runs_where = "rr.user_id = :u"
    fb_where = "f.user_id = :u"
    if since is not None:
        params["since"] = since
        runs_where += " AND rr.created_at >= :since"
        fb_where += " AND f.created_at >= :since"

    activity_sql = f"""
        SELECT
            date_trunc('day', ts)::date AS bucket,
            SUM(CASE WHEN kind = 'run' THEN 1 ELSE 0 END) AS run_started,
            SUM(CASE WHEN kind = 'viewed' THEN 1 ELSE 0 END) AS viewed,
            SUM(CASE WHEN kind = 'liked' THEN 1 ELSE 0 END) AS liked,
            SUM(CASE WHEN kind = 'applied' THEN 1 ELSE 0 END) AS applied
        FROM (
            SELECT rr.created_at AS ts, 'run' AS kind
            FROM core.recommendation_runs rr
            WHERE {runs_where}
            UNION ALL
            SELECT f.created_at, f.signal
            FROM core.feedback f
            WHERE {fb_where}
        ) t
        GROUP BY bucket
        ORDER BY bucket
    """
    activity_rows = (await session.execute(text(activity_sql), params)).mappings().all()

    activity_series = [
        {
            "bucket": r["bucket"].isoformat(),
            "run_started": int(r["run_started"] or 0),
            "viewed": int(r["viewed"] or 0),
            "liked": int(r["liked"] or 0),
            "applied": int(r["applied"] or 0),
        }
        for r in activity_rows
    ]

    # 5. Рекомендации по программам (за всё время)
    rec_stats_rows = (await session.execute(text("""
        SELECT programme_kind, COUNT(*) AS cnt
        FROM core.recommendation_items ri
        JOIN core.recommendation_runs rr ON rr.run_id = ri.run_id
        WHERE rr.user_id = :u AND rr.state = 'succeeded'
        GROUP BY programme_kind
    """), {"u": user.user_id})).mappings().all()
    recommendation_statistics = [
        {"programme_kind": r["programme_kind"], "count": int(r["cnt"])} for r in rec_stats_rows
    ]

    return {
        "profile_completeness": {"percent": percent, "filled": filled, "total": total},
        "programme_distribution": programme_distribution,
        "interests_distribution": interests_distribution,
        "activity_series": activity_series,
        "recommendation_statistics": recommendation_statistics,
    }