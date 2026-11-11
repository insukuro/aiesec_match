import logging
import time
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.deps import get_catalog_reader
from app.domain.filters import hard_filter
from app.domain.profile import build_profile
from app.domain.scoring import rank_programme
from app.schemas import MatchRequest, MatchResponse

log = logging.getLogger("matcher")
router = APIRouter(prefix="/v1", tags=["match"])
STRATEGIES = {"weighted_v1"}


def route_programmes(req: MatchRequest) -> Dict[str, float]:
    """Роутер v0 из ТЗ 2.2: какие программы искать и с каким приором."""
    explicit = req.filters.programme_kinds or req.profile.programmes
    if explicit:
        return {k: 1.0 for k in dict.fromkeys(explicit)}       # без дублей, порядок сохранён
    kinds = []
    spheres = req.profile.spheres
    if any(s.startswith("teaching_") for s in spheres):
        kinds.append("teacher")
    if any(not s.startswith("teaching_") for s in spheres):
        kinds.append("talent")
    if req.profile.activities:
        kinds.append("volunteer")
    return {k: round(1 / len(kinds), 3) for k in kinds}


@router.post("/match", response_model=MatchResponse)
def match(req: MatchRequest,
          reader=Depends(get_catalog_reader),
          s: Settings = Depends(get_settings)):
    started = time.perf_counter()

    if req.strategy and req.strategy not in STRATEGIES:
        raise HTTPException(422, detail={"type": "unknown-strategy"})
    prior = route_programmes(req)
    if not prior:
        raise HTTPException(422, detail={"type": "profile-incomplete", "missing": ["programmes"]})

    p = build_profile(req.profile)
    groups = []
    for kind in prior:
        min_en = s.min_english.get(kind, "B1")
        try:
            opps = reader.list_open(kind)
        except Exception as e:                       # БД недоступна
            log.exception("catalog read failed kind=%s", kind)
            raise HTTPException(503, detail={"type": "catalog-unavailable"}) from e
        cands = hard_filter(opps, p, req.filters, min_en)
        groups.append(rank_programme(cands, p, kind, p.languages_for(min_en),
                                     req.limit_per_programme, req.explain,
                                     s.label_excellent, s.label_good))

    took = int((time.perf_counter() - started) * 1000)
    log.info("match profile_id=%s kinds=%s took_ms=%s", req.profile_id, list(prior), took)
    return MatchResponse(request_id=req.request_id, profile_id=req.profile_id,
                         programme_prior=prior, took_ms=took, groups=groups)