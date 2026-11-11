import math
from bisect import bisect_left
from datetime import date
from typing import Dict, List, Set

from app.domain.models import Opportunity
from app.domain.profile import Profile

OPTION_WT = {"required": 1.0, "preferred": 0.5}
NEUTRAL = 0.5          # «не знаем» = середина, ни плюс ни минус


def coverage(reqs: Dict[int, str], have: Set[int]) -> float:
    """Доля требований (с весом required/preferred), которую закрывает кандидат."""
    if not reqs:
        return NEUTRAL
    total = sum(OPTION_WT.get(opt, 1.0) for opt in reqs.values())
    got = sum(OPTION_WT.get(opt, 1.0) for cid, opt in reqs.items() if cid in have)
    return got / total


def language_score(o: Opportunity, langs: Set[int]) -> float:
    preferred = {cid for cid, opt in o.languages.items() if opt == "preferred"}
    if not preferred:
        return NEUTRAL
    return len(preferred & langs) / len(preferred)


def city_score(o: Opportunity, p: Profile) -> float:
    if not p.preferred_lc_ids:
        return NEUTRAL
    return 1.0 if o.lc_id in p.preferred_lc_ids else 0.0


def duration_score(o: Opportunity, p: Profile) -> float:
    if o.duration_weeks is None or (p.min_weeks is None and p.max_weeks is None):
        return NEUTRAL
    lo = p.min_weeks if p.min_weeks is not None else 0
    hi = p.max_weeks if p.max_weeks is not None else 10**6
    d = o.duration_weeks
    dist = lo - d if d < lo else d - hi if d > hi else 0
    return max(0.0, 1 - dist / 8)          # спад до 0 на расстоянии 8 недель


def cost_score(o: Opportunity, p: Profile) -> float:
    if o.cost_total == 0:
        return 1.0
    if o.cost_total is None or p.max_budget_eur is None or o.cost_currency not in (None, "EUR"):
        return NEUTRAL
    return 1.0 if o.cost_total <= p.max_budget_eur else 0.0


def freshness_score(o: Opportunity, today: date) -> float:
    if o.date_opened is None:
        return NEUTRAL
    return math.exp(-(today - o.date_opened).days / 90)


def chance_scores(opps: List[Opportunity], a: float = 10.0) -> Dict[int, float]:
    """Шанс на принятие: сглаженная доля принятых × доля свободных мест, затем процентиль."""
    if not opps:
        return {}
    apps = sum(o.applicants_count for o in opps)
    p0 = sum(o.accepted_count for o in opps) / apps if apps else 0.0
    raw = {}
    for o in opps:
        rate = (o.accepted_count + a * p0) / (o.applicants_count + a)
        free = o.available_openings / o.openings if o.openings else 1.0
        raw[o.opportunity_id] = rate * free
    values = sorted(raw.values())
    if values[0] == values[-1]:
        return {oid: NEUTRAL for oid in raw}
    n = len(values)
    return {oid: bisect_left(values, v) / (n - 1) for oid, v in raw.items()}


def compute_features(o: Opportunity, p: Profile, langs: Set[int],
                     chance: float, today: date) -> Dict[str, float]:
    return {
        "background": coverage(o.backgrounds, p.background_ids),
        "skill": coverage(o.skills, p.skill_ids),
        "language": language_score(o, langs),
        "city": city_score(o, p),
        "duration": duration_score(o, p),
        "cost": cost_score(o, p),
        "chance": chance,
        "freshness": freshness_score(o, today),
    }