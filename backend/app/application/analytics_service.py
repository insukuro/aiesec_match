from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Date, case, func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.models import (
    Feedback, Profile, ProfileVersion, RecommendationItem, RecommendationRun,
)
from ..schemas import AnalyticsOut

PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90, "all": None}
EXPECTED_KEYS = [
    "programmes", "english_level", "study", "work_experience",
    "spheres", "activities", "desired_countries", "duration",
    "start_window", "motivation_text", "financial",
]


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def me(self, user_id, period: str, from_: str | None) -> AnalyticsOut:
        since = self._since(period, from_)

        # 1. Заполненность профиля
        body = await self._profile_body(user_id)
        filled = sum(1 for k in EXPECTED_KEYS if body.get(k) not in (None, "", [], {}))
        total = len(EXPECTED_KEYS)
        percent = round(filled / total * 100) if total else 0

        # 2. Распределение по программам (последний успешный run)
        programme_distribution = await self._programme_distribution(user_id)

        # 3. Интересы
        spheres = body.get("spheres") or []
        interests_distribution = [{"code": s, "label": s, "count": 1} for s in spheres]

        # 4. Активность по дням
        activity_series = await self._activity(user_id, since)

        # 5. Статистика рекомендаций (за всё время)
        recommendation_statistics = await self._recommendation_statistics(user_id)

        return AnalyticsOut(
            profile_completeness={"percent": percent, "filled": filled, "total": total},
            programme_distribution=programme_distribution,
            interests_distribution=interests_distribution,
            activity_series=activity_series,
            recommendation_statistics=recommendation_statistics,
        )

    @staticmethod
    def _since(period: str, frm: str | None) -> datetime | None:
        if frm:
            return datetime.fromisoformat(frm).replace(tzinfo=timezone.utc)
        days = PERIOD_DAYS.get(period)
        if days is None:
            return None
        return datetime.now(timezone.utc) - timedelta(days=days)

    async def _profile_body(self, user_id) -> dict[str, Any]:
        row = (await self._s.execute(
            select(Profile.current_version, ProfileVersion.body)
            .outerjoin(
                ProfileVersion,
                (ProfileVersion.user_id == Profile.user_id)
                & (ProfileVersion.version == Profile.current_version),
            )
            .where(Profile.user_id == user_id)
        )).one_or_none()
        if row is None or row.body is None:
            return {}
        return dict(row.body)

    async def _last_successful_run_id(self, user_id):
        return (await self._s.execute(
            select(RecommendationRun.run_id)
            .where(
                RecommendationRun.user_id == user_id,
                RecommendationRun.state == "succeeded",
            )
            .order_by(RecommendationRun.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

    async def _programme_distribution(self, user_id) -> list[dict]:
        run_id = await self._last_successful_run_id(user_id)
        if run_id is None:
            return []
        rows = (await self._s.execute(
            select(
                RecommendationItem.programme_kind,
                func.count().label("cnt"),
            )
            .where(RecommendationItem.run_id == run_id)
            .group_by(RecommendationItem.programme_kind)
        )).all()
        return [
            {"programme_kind": r.programme_kind, "count": int(r.cnt)}
            for r in rows
        ]

    async def _recommendation_statistics(self, user_id) -> list[dict]:
        rows = (await self._s.execute(
            select(
                RecommendationItem.programme_kind,
                func.count().label("cnt"),
            )
            .join(RecommendationRun, RecommendationRun.run_id == RecommendationItem.run_id)
            .where(
                RecommendationRun.user_id == user_id,
                RecommendationRun.state == "succeeded",
            )
            .group_by(RecommendationItem.programme_kind)
        )).all()
        return [
            {"programme_kind": r.programme_kind, "count": int(r.cnt)}
            for r in rows
        ]

    async def _activity(self, user_id, since: datetime | None) -> list[dict]:
        runs = select(
            RecommendationRun.created_at.label("ts"),
            literal("run").label("kind"),
        ).where(RecommendationRun.user_id == user_id)
        fb = select(
            Feedback.created_at.label("ts"),
            Feedback.signal.label("kind"),
        ).where(Feedback.user_id == user_id)
        if since is not None:
            runs = runs.where(RecommendationRun.created_at >= since)
            fb = fb.where(Feedback.created_at >= since)

        union = union_all(runs, fb).subquery("t")
        bucket = func.date_trunc("day", union.c.ts).cast(Date).label("bucket")
        stmt = (
            select(
                bucket,
                func.sum(case((union.c.kind == "run", 1), else_=0)).label("run_started"),
                func.sum(case((union.c.kind == "viewed", 1), else_=0)).label("viewed"),
                func.sum(case((union.c.kind == "liked", 1), else_=0)).label("liked"),
                func.sum(case((union.c.kind == "applied", 1), else_=0)).label("applied"),
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        rows = (await self._s.execute(stmt)).all()
        return [
            {
                "bucket": r.bucket.isoformat(),
                "run_started": int(r.run_started or 0),
                "viewed": int(r.viewed or 0),
                "liked": int(r.liked or 0),
                "applied": int(r.applied or 0),
            }
            for r in rows
        ]