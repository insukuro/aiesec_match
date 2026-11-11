from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional, Set

@dataclass
class Opportunity:
    opportunity_id: int
    programme_kind: str                      # talent | teacher | volunteer
    title: str = ""
    family_key: Optional[str] = None
    country_code: Optional[str] = None
    lc_id: Optional[int] = None
    is_open: bool = True
    openings: int = 0
    available_openings: int = 1
    applicants_count: int = 0
    accepted_count: int = 0
    date_opened: Optional[date] = None
    applications_close_date: Optional[date] = None
    duration_weeks: Optional[int] = None
    cost_total: Optional[float] = None
    cost_currency: Optional[str] = None
    # требования: constant_id -> option ("required" | "preferred")
    backgrounds: Dict[int, str] = field(default_factory=dict)
    skills: Dict[int, str] = field(default_factory=dict)
    languages: Dict[int, str] = field(default_factory=dict)
    study_levels: Set[int] = field(default_factory=set)
    nationalities: Set[int] = field(default_factory=set)