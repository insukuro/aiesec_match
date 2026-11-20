from __future__ import annotations

from sqlalchemy import String, case, func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.models import Feedback, RecommendationRun
from ..infrastructure.time_utils import parse_dt


class HistoryService:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def list(
        self,
        user_id,
        *,
        type: str | None,
        frm: str | None,
        to: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        since = parse_dt(frm)
        until = parse_dt(to)

        include_runs = type is None or type == "run_finished"
        include_feedback = type is None or type.startswith("signal_")
        signal_filter = type[len("signal_"):] if (type and type.startswith("signal_")) else None

        parts = []

        if include_runs:
            runs = (
                select(
                    literal("run_finished").label("event_type"),
                    RecommendationRun.finished_at.label("occurred_at"),
                    literal("Подбор завершён").label("title"),
                    func.concat(
                        literal("Найдено "),
                        func.coalesce(RecommendationRun.total_candidates, 0),
                        literal(" кандидатов"),
                    ).label("description"),
                    func.cast(RecommendationRun.run_id, String).label("entity_id"),
                )
                .where(
                    RecommendationRun.user_id == user_id,
                    RecommendationRun.state == "succeeded",
                    RecommendationRun.finished_at.is_not(None),
                )
            )
            if since is not None:
                runs = runs.where(RecommendationRun.finished_at >= since)
            if until is not None:
                runs = runs.where(RecommendationRun.finished_at <= until)
            parts.append(runs)

        if include_feedback:
            title_expr = case(
                (Feedback.signal == "liked", literal("Понравилось")),
                (Feedback.signal == "disliked", literal("Не понравилось")),
                (Feedback.signal == "hidden", literal("Скрыто")),
                (Feedback.signal == "applied", literal("Отклик отправлен")),
                (Feedback.signal == "opened", literal("Открыто")),
                else_=Feedback.signal,
            )
            fb = (
                select(
                    func.concat(literal("signal_"), Feedback.signal).label("event_type"),
                    Feedback.created_at.label("occurred_at"),
                    title_expr.label("title"),
                    func.concat(
                        literal("Вакансия #"),
                        func.cast(Feedback.opportunity_id, String),
                    ).label("description"),
                    func.cast(Feedback.opportunity_id, String).label("entity_id"),
                )
                .where(Feedback.user_id == user_id)
            )
            if signal_filter is not None:
                fb = fb.where(Feedback.signal == signal_filter)
            if since is not None:
                fb = fb.where(Feedback.created_at >= since)
            if until is not None:
                fb = fb.where(Feedback.created_at <= until)
            parts.append(fb)

        if not parts:
            return {"items": [], "total": 0, "limit": limit, "offset": offset}

        union = union_all(*parts).subquery("events")

        rows = (await self._s.execute(
            select(
                union.c.event_type,
                union.c.occurred_at,
                union.c.title,
                union.c.description,
                union.c.entity_id,
            )
            .order_by(union.c.occurred_at.desc())
            .limit(limit).offset(offset)
        )).all()

        total = (await self._s.execute(
            select(func.count()).select_from(union)
        )).scalar_one()

        items = [
            {
                "event_id": f"{r.event_type}:{r.entity_id}:{r.occurred_at.isoformat()}",
                "type": r.event_type,
                "occurred_at": r.occurred_at,
                "title": r.title,
                "description": r.description,
                "related_entity_id": r.entity_id,
            }
            for r in rows
        ]
        return {"items": items, "total": int(total), "limit": limit, "offset": offset}