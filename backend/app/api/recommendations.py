import hashlib, hmac, uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import require_registered
from ..catalog import current_watermark, fetch_cards, fetch_requirements
from ..completeness import missing_for_match
from ..config import get_settings
from ..db import get_session
from ..errors import ProfileIncomplete, ProfileNotFound, RunNotFound
from ..matcher_client import MatcherClient, get_matcher
from ..models import Profile, ProfileVersion, RecommendationItem, RecommendationRun, User
from ..schemas import RecommendationRunIn

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _profile_hash(user_id: uuid.UUID) -> str:
    return hmac.new(
        get_settings().profile_hmac_secret.encode(), str(user_id).encode(), hashlib.sha256
    ).hexdigest()[:32]


def _label(score: float) -> str:
    return "excellent" if score >= 0.8 else "good" if score >= 0.6 else "fair"


def _programme_prior(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, dict):
        return list(value.keys())
    return list(value)


@router.post("")
async def create_run(
    body: RecommendationRunIn,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8),
    user: User = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
    matcher: MatcherClient = Depends(get_matcher),
    response: Response = None,
):
    existing = (await session.execute(
        select(RecommendationRun).where(
            RecommendationRun.user_id == user.user_id,
            RecommendationRun.idempotency_key == idempotency_key,
        )
    )).scalar_one_or_none()
    if existing:
        return await _assemble(session, existing)

    p = await session.get(Profile, user.user_id)
    if p is None:
        raise ProfileNotFound()
    v = await session.get(ProfileVersion, (user.user_id, p.current_version))
    miss = missing_for_match(v.body)
    if miss:
        raise ProfileIncomplete(errors=[{"loc": ["profile", m]} for m in miss])

    run = RecommendationRun(
        user_id=user.user_id, profile_version=p.current_version,
        filters=body.filters or {}, idempotency_key=idempotency_key,
        state="running", model_versions={}, created_at=datetime.now(timezone.utc),
    )
    session.add(run)
    await session.flush()

    snapshot = {
        k: v.body.get(k) for k in (
            "programmes", "english_level", "study", "work_experience", "spheres", "activities",
            "desired_countries", "duration", "start_window", "financial", "nationality",
        )
        if v.body.get(k) is not None
    }

    f = body.filters or {}
    payload = {
        "request_id": str(run.run_id),
        "profile_id": _profile_hash(user.user_id),
        "profile": snapshot,
        "filters": {
            "programme_kinds": f.get("programme_kinds", []),
            "country_codes": f.get("country_codes", []),
            "exclude_opportunity_ids": f.get("exclude_opportunity_ids", []),
        },
        "limit_per_programme": body.limit_per_programme,
        "explain": True,
    }
    try:
        result = await matcher.match(payload)
    except Exception as e:
        run.state = "failed"
        run.error = str(e)
        run.finished_at = datetime.now(timezone.utc)
        await session.commit()
        raise

    watermark = await current_watermark(session)
    groups = result.get("groups", [])
    all_ids = [it["opportunity_id"] for g in groups for it in g["items"]]
    cards = await fetch_cards(session, all_ids)
    reqs = await fetch_requirements(session, all_ids)
    for g in groups:
        for rank, it in enumerate(g["items"], start=1):
            if it["opportunity_id"] not in cards or not cards[it["opportunity_id"]]["is_open"]:
                continue
            session.add(RecommendationItem(
                run_id=run.run_id, programme_kind=g["programme_kind"], rank=rank,
                opportunity_id=it["opportunity_id"],
                family_key=cards[it["opportunity_id"]]["family_key"],
                score=it["score"], breakdown=it.get("breakdown", {}),
                reasons=it.get("reasons", []),
            ))

    run.state = "succeeded"
    run.finished_at = datetime.now(timezone.utc)
    run.catalog_watermark = watermark
    run.programme_prior = _programme_prior(result.get("programme_prior"))
    run.total_candidates = sum(g.get("total_candidates", 0) for g in groups)
    await session.commit()

    if response is not None:
        response.status_code = 202 if body.mode == "async" else 200
    return await _assemble(session, run)


async def _assemble(session: AsyncSession, run: RecommendationRun) -> dict:
    items = (await session.execute(
        select(RecommendationItem).where(RecommendationItem.run_id == run.run_id)
        .order_by(RecommendationItem.programme_kind, RecommendationItem.rank)
    )).scalars().all()
    ids = [i.opportunity_id for i in items]
    cards = await fetch_cards(session, ids)
    reqs = await fetch_requirements(session, ids)

    groups: dict[str, dict] = {}
    for it in items:
        c = cards.get(it.opportunity_id)
        if c is None or not c["is_open"]:
            continue
        g = groups.setdefault(it.programme_kind, {
            "programme_kind": it.programme_kind, "total_candidates": 0, "items": [],
        })
        g["items"].append({
            "rank": it.rank, "score": float(it.score), "label": _label(float(it.score)),
            "family": {"family_key": c["family_key"], "siblings_count": 0},
            "opportunity": _card(c, reqs.get(it.opportunity_id, [])),
            "reasons": it.reasons,
        })
    prior = _programme_prior(run.programme_prior) or list(groups.keys())
    ordered = [groups[k] for k in prior if k in groups]
    return {
        "run_id": str(run.run_id), "state": run.state,
        "profile_version": run.profile_version, "strategy": run.strategy,
        "created_at": run.created_at, "finished_at": run.finished_at,
        "catalog_watermark": run.catalog_watermark,
        "programme_prior": prior, "degraded": False,
        "groups": ordered, "error": run.error,
    }


def _card(c: dict, reqs: list[dict]) -> dict:
    return {
        "opportunity_id": c["opportunity_id"], "title": c["title"], "family_key": c["family_key"],
        "programme": {"id": c["programme_id"], "kind": c["programme_kind"],
                      "name": c.get("programme_kind") or c["programme_kind"]},
        "place": {"country_code": c["country_code"], "country_name": c["country_name"],
                  "lc_id": c["lc_id"], "lc_name": c["lc_name"], "location": c["location"]},
        "organisation_name": c["organisation_name"],
        "capacity": {"openings": c["openings"], "available_openings": c["available_openings"],
                     "applicants_count": c["applicants_count"], "accepted_count": c["accepted_count"]},
        "duration_weeks": c["duration_weeks"],
        "cost": ({"amount": float(c["cost_total"]), "currency": c["cost_currency"]}
                 if c["cost_total"] is not None else None),
        "requirements": [
            {"kind": r["kind"], "constant_id": r["constant_id"], "name": r["constant_name"],
             "parent_name": r["parent_name"], "option": r["option"]}
            for r in reqs
        ],
        "date_opened": c["date_opened"], "applications_close_date": c["applications_close_date"],
        "is_open": c["is_open"], "updated_at": c["updated_at"],
    }


@router.get("/latest")
async def latest(user: User = Depends(require_registered),
                 session: AsyncSession = Depends(get_session)):
    run = (await session.execute(
        select(RecommendationRun).where(
            RecommendationRun.user_id == user.user_id,
            RecommendationRun.state == "succeeded",
        ).order_by(RecommendationRun.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if run is None:
        raise RunNotFound()
    return await _assemble(session, run)


@router.get("/{run_id}")
async def get_run(run_id: uuid.UUID, user: User = Depends(require_registered),
                  session: AsyncSession = Depends(get_session)):
    run = await session.get(RecommendationRun, run_id)
    if run is None or run.user_id != user.user_id:
        raise RunNotFound()
    return await _assemble(session, run)