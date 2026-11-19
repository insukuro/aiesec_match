from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..domain.completeness import missing_for_match
from ..domain.scoring import label, programme_prior
from ..errors import ConsentRequired, ProfileIncomplete, ProfileNotFound, RunNotFound
from ..infrastructure.matcher_client import MatcherClient
from ..infrastructure.repositories.catalog_repo import CatalogRepo
from ..infrastructure.repositories.consent_repo import ConsentRepo
from ..infrastructure.repositories.feedback_repo import FeedbackRepo
from ..infrastructure.repositories.profile_repo import ProfileRepo
from ..infrastructure.repositories.run_repo import RunRepo
from ..schemas import RecommendationRunIn
from .dto_mappers import card_dto


def _profile_hash(user_id: uuid.UUID) -> str:
    return hmac.new(
        get_settings().profile_hmac_secret.encode(), str(user_id).encode(), hashlib.sha256
    ).hexdigest()[:32]


class MatchingService:
    def __init__(self, session: AsyncSession, matcher: MatcherClient):
        self._s = session
        self._matcher = matcher
        self._runs = RunRepo(session)
        self._profiles = ProfileRepo(session)
        self._catalog = CatalogRepo(session)
        self._feedback = FeedbackRepo(session)
        self._consents = ConsentRepo(session)

    async def create_run(
        self,
        user_id: uuid.UUID,
        body: RecommendationRunIn,
        idempotency_key: str,
    ) -> dict:
        existing = await self._runs.get_by_idempotency(user_id, idempotency_key)
        if existing is not None:
            return await self._assemble(existing)

        if not await self._consents.has(user_id, "pd_processing"):
            raise ConsentRequired()

        p = await self._profiles.get(user_id)
        if p is None:
            raise ProfileNotFound()
        v = await self._profiles.get_version(user_id, p.current_version)
        miss = missing_for_match(v.body)
        if miss:
            raise ProfileIncomplete(errors=[{"loc": ["profile", m]} for m in miss])

        run = await self._runs.create(
            user_id=user_id,
            profile_version=p.current_version,
            filters=body.filters or {},
            idempotency_key=idempotency_key,
        )

        snapshot = {
            k: v.body.get(k) for k in (
                "programmes", "english_level", "study", "work_experience", "spheres",
                "activities", "desired_countries", "duration", "start_window",
                "financial", "nationality",
            )
            if v.body.get(k) is not None
        }

        f = body.filters or {}
        user_excluded = set(f.get("exclude_opportunity_ids", []))
        hidden = set(await self._feedback.ids_by_signals(user_id, ["hidden", "disliked"]))
        exclude_ids = list(user_excluded | hidden)

        payload = {
            "request_id": str(run.run_id),
            "profile_id": _profile_hash(user_id),
            "profile": snapshot,
            "filters": {
                "programme_kinds": f.get("programme_kinds", []),
                "country_codes": f.get("country_codes", []),
                "exclude_opportunity_ids": exclude_ids,
            },
            "limit_per_programme": body.limit_per_programme,
            "explain": True,
        }

        try:
            result = await self._matcher.match(payload)
        except Exception as e:
            run.state = "failed"
            run.error = str(e)
            run.finished_at = datetime.now(timezone.utc)
            await self._s.commit()
            raise

        watermark = await self._catalog.current_watermark()
        groups = result.get("groups", [])
        all_ids = [it["opportunity_id"] for g in groups for it in g["items"]]
        cards = await self._catalog.fetch_cards(all_ids)

        for g in groups:
            for rank, it in enumerate(g["items"], start=1):
                c = cards.get(it["opportunity_id"])
                if c is None or not c.is_open:
                    continue
                await self._runs.add_item(
                    run_id=run.run_id,
                    programme_kind=g["programme_kind"],
                    rank=rank,
                    opportunity_id=it["opportunity_id"],
                    family_key=c.family_key,
                    score=it["score"],
                    breakdown=it.get("breakdown", {}),
                    reasons=it.get("reasons", []),
                )

        run.state = "succeeded"
        run.finished_at = datetime.now(timezone.utc)
        run.catalog_watermark = watermark
        run.programme_prior = programme_prior(result.get("programme_prior"))
        run.total_candidates = sum(g.get("total_candidates", 0) for g in groups)
        await self._s.commit()

        return await self._assemble(run)

    async def latest(self, user_id: uuid.UUID) -> dict:
        run = await self._runs.latest_succeeded(user_id)
        if run is None:
            raise RunNotFound()
        return await self._assemble(run)

    async def get_run(self, user_id: uuid.UUID, run_id: uuid.UUID) -> dict:
        run = await self._runs.get(run_id)
        if run is None or run.user_id != user_id:
            raise RunNotFound()
        return await self._assemble(run)

    async def list_runs(
        self, user_id: uuid.UUID, limit: int, offset: int,
    ) -> dict:
        rows, total = await self._runs.list_for_user(user_id, limit, offset)
        items = [
            {
                "run_id": str(r.run_id),
                "state": r.state,
                "profile_version": r.profile_version,
                "total_candidates": r.total_candidates,
                "created_at": r.created_at,
                "finished_at": r.finished_at,
                "error": r.error,
            }
            for r in rows
        ]
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    async def _assemble(self, run) -> dict:
        items = await self._runs.items_for(run.run_id)
        ids = [i.opportunity_id for i in items]
        cards = await self._catalog.fetch_cards(ids)
        reqs = await self._catalog.fetch_requirements(ids)

        hidden = set(await self._feedback.ids_by_signals(run.user_id, ["hidden", "disliked"]))
        liked = set(await self._feedback.ids_by_signals(run.user_id, ["liked"]))

        groups: dict[str, dict] = {}
        for it in items:
            c = cards.get(it.opportunity_id)
            if c is None or not c.is_open:
                continue
            g = groups.setdefault(it.programme_kind, {
                "programme_kind": it.programme_kind,
                "total_candidates": 0,
                "items": [],
            })
            g["items"].append({
                "rank": it.rank,
                "score": float(it.score),
                "label": label(float(it.score)),
                "family": {"family_key": c.family_key, "siblings_count": 0},
                "opportunity": card_dto(c, reqs.get(it.opportunity_id, [])),
                "reasons": it.reasons,
                "liked": it.opportunity_id in liked,
                "hidden": it.opportunity_id in hidden,
            })

        prior = programme_prior(run.programme_prior) or list(groups.keys())
        ordered = [groups[k] for k in prior if k in groups]
        return {
            "run_id": str(run.run_id),
            "state": run.state,
            "profile_version": run.profile_version,
            "strategy": run.strategy,
            "created_at": run.created_at,
            "finished_at": run.finished_at,
            "catalog_watermark": run.catalog_watermark,
            "programme_prior": prior,
            "degraded": False,
            "groups": ordered,
            "error": run.error,
        }