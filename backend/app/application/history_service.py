from __future__ import annotations

from typing import Any

from sqlalchemy import case, literal, select, union_all
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
                    literal("run_finished").label("type"),
                    RecommendationRun.finished_at.label("occurred_at"),
                    literal("Подбор завершён").label("title"),
                    ("Найдено " + RecommendationRun.total_candidates.cast(str) + " кандидатов").label("description"),
                    RecommendationRun.run_id.cast(str).label("related_entity_id"),
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
                (Feedback.signal == "liked", "Понравилось"),
                (Feedback.signal == "disliked", "Не понравилось"),
                (Feedback.signal == "hidden", "Скрыто"),
                (Feedback.signal == "applied", "Отклик отправлен"),
                (Feedback.signal == "opened", "Открыто"),
                else_=Feedback.signal,
            )
            fb = (
                select(
                    ("signal_" + Feedback.signal).label("type"),
                    Feedback.created_at.label("occurred_at"),
                    title_expr.label("title"),
                    ("Вакансия #" + Feedback.opportunity_id.cast(str)).label("description"),
                    Feedback.opportunity_id.cast(str).label("related_entity_id"),
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
            select(union)
            .order_by(union.c.occurred_at.desc())
            .limit(limit).offset(offset)
        )).all()
        total = (await self._s.execute(
            select(union.c.type).select_from(union).with_only_columns(
                __import__("sqlalchemy").func.count()
            )
        )).scalar_one()

        items = [
            {
                "event_id": f"{r.type}:{r.related_entity_id}:{r.occurred_at.isoformat()}",
                "type": r.type,
                "occurred_at": r.occurred_at,
                "title": r.title,
                "description": r.description,
                "related_entity_id": r.related_entity_id,
            }
            for r in rows
        ]
        return {"items": items, "total": int(total), "limit": limit, "offset": offset}