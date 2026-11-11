from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

from app.domain.features import chance_scores, compute_features
from app.domain.models import Opportunity
from app.domain.profile import Profile
from app.schemas import MatchItem, ProgrammeGroup, Reason

REASONS = {
    "background": ("background_match", "Ваше образование подходит под требования"),
    "skill": ("skill_match", "Ваши навыки совпадают с нужными"),
    "language": ("language_preferred", "Вы знаете желательные языки"),
    "city": ("city_pref", "Город из ваших предпочтений"),
    "duration": ("duration_fit", "Длительность в вашем диапазоне"),
    "cost": ("cost_fit", "Укладывается в бюджет"),
    "chance": ("chance_high", "Хорошие шансы на принятие"),
    "freshness": ("fresh", "Вакансия открылась недавно"),
}


@lru_cache
def load_weights() -> dict:
    with open(Path(__file__).resolve().parent.parent / "weights.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def label(score: float, excellent: float, good: float) -> str:
    return "excellent" if score >= excellent else "good" if score >= good else "fair"


def make_reasons(f: Dict[str, float], w: Dict[str, float]) -> List[Reason]:
    pos = sorted(((w[k] * v, k) for k, v in f.items() if w.get(k, 0) > 0 and v >= 0.7), reverse=True)
    out = [Reason(code=REASONS[k][0], polarity="positive", weight=round(c, 3), text=REASONS[k][1])
           for c, k in pos[:3]]
    if w.get("chance", 0) > 0 and f["chance"] < 0.3:
        out.append(Reason(code="chance_low", polarity="negative",
                          weight=round(w["chance"] * (1 - f["chance"]), 3),
                          text="Высокая конкуренция на эту вакансию"))
    return out


def rank_programme(opps: List[Opportunity], p: Profile, kind: str, langs: Set[int],
                   limit: int, explain: bool, excellent: float, good: float,
                   today: Optional[date] = None) -> ProgrammeGroup:
    today = today or date.today()
    w = load_weights()[kind]
    chance = chance_scores(opps)

    scored = []
    for o in opps:
        f = compute_features(o, p, langs, chance[o.opportunity_id], today)
        u = sum(w.get(k, 0) * v for k, v in f.items())
        scored.append((u, o, f))
    scored.sort(key=lambda t: (-t[0], t[1].opportunity_id))   # детерминированный порядок

    # схлопывание семей: от каждой семьи остаётся лучшая вакансия
    best, siblings = [], {}
    for u, o, f in scored:
        key = o.family_key or f"id:{o.opportunity_id}"
        if key in siblings:
            siblings[key] += 1
            continue
        siblings[key] = 0
        best.append((u, o, f, key))

    items = [
        MatchItem(
            opportunity_id=o.opportunity_id, rank=rank, score=round(u, 4),
            label=label(u, excellent, good), family_key=o.family_key,
            siblings_count=siblings[key],
            reasons=make_reasons(f, w) if explain else [],
            breakdown={k: round(v, 4) for k, v in f.items()},
        )
        for rank, (u, o, f, key) in enumerate(best[:limit], start=1)
    ]
    return ProgrammeGroup(programme_kind=kind, total_candidates=len(opps), items=items)