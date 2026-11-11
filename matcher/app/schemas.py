from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

ProgrammeKind = Literal["talent", "teacher", "volunteer"]

class ProfileSnapshot(BaseModel):
    model_config = ConfigDict(extra="allow")   # новые поля бэка не ломают нас
    programmes: List[ProgrammeKind] = []
    english_level: Optional[Literal["A1","A2","B1","B2","C1","C2"]] = None
    study: Optional[Dict[str, Any]] = None
    work_experience: Optional[str] = None
    spheres: List[str] = []
    activities: List[str] = []
    desired_countries: List[str] = []
    duration: Optional[Dict[str, int]] = None
    start_window: Optional[str] = None
    financial: Optional[Dict[str, Any]] = None
    nationality: Optional[str] = None
    preferred_lc_ids: List[int] = []
    other_languages: List[str] = []

class MatchFilters(BaseModel):
    programme_kinds: List[ProgrammeKind] = []
    country_codes: List[str] = []
    exclude_opportunity_ids: List[int] = []

class MatchRequest(BaseModel):
    request_id: Optional[str] = None     # бэк пока не шлёт
    profile_id: Optional[str] = None
    profile: ProfileSnapshot
    filters: MatchFilters = MatchFilters()
    strategy: Optional[str] = None
    limit_per_programme: int = Field(10, ge=1, le=50)
    explain: bool = True

class Reason(BaseModel):
    code: str
    polarity: Literal["positive", "negative"]
    weight: float
    text: str

class MatchItem(BaseModel):
    opportunity_id: int
    rank: int
    score: float
    label: Literal["excellent", "good", "fair"]
    reasons: List[Reason] = []
    breakdown: Dict[str, float] = {}
    family_key: Optional[str] = None
    siblings_count: int = 0

class ProgrammeGroup(BaseModel):
    programme_kind: ProgrammeKind
    total_candidates: int
    items: List[MatchItem]

class MatchResponse(BaseModel):
    request_id: Optional[str] = None
    profile_id: Optional[str] = None
    strategy: str = "weighted_v1"
    programme_prior: Dict[str, float] = {}
    degraded: List[str] = []
    took_ms: int = 0
    groups: List[ProgrammeGroup] = []

class Dictionary(BaseModel):
    id: int
    name: str

class HealthResponse(BaseModel):
    status: str = "ok"