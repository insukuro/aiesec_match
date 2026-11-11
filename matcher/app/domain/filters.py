from datetime import date
from typing import List, Optional

from app.domain.models import Opportunity
from app.domain.profile import Profile
from app.schemas import MatchFilters


def hard_filter(opps: List[Opportunity], p: Profile, filters: MatchFilters,
                min_english: str, today: Optional[date] = None) -> List[Opportunity]:
    today = today or date.today()
    langs = p.languages_for(min_english)
    out = []
    for o in opps:
        # открыта и есть места
        if not o.is_open or o.available_openings <= 0:
            continue
        # срок подачи не прошёл
        if o.applications_close_date and o.applications_close_date < today:
            continue
        # все ОБЯЗАТЕЛЬНЫЕ языки вакансии есть у кандидата
        required = {cid for cid, opt in o.languages.items() if opt == "required"}
        if not required <= langs:
            continue
        # гражданство (если кандидат его не указал, не режем)
        if o.nationalities and p.nationality_id is not None and p.nationality_id not in o.nationalities:
            continue
        # уровень учёбы (если обе стороны его знают)
        if o.study_levels and p.study_level_ids and not (o.study_levels & p.study_level_ids):
            continue
        # бюджет: платная вакансия и кандидат не готов платить или не укладывается
        if o.cost_total and o.cost_total > 0:
            if p.willing_to_pay is False:
                continue
            if (p.max_budget_eur is not None and o.cost_currency in (None, "EUR")
                    and o.cost_total > p.max_budget_eur):
                continue
        # фильтры из запроса
        if filters.country_codes and o.country_code not in filters.country_codes:
            continue
        if o.opportunity_id in filters.exclude_opportunity_ids:
            continue
        out.append(o)
    return out