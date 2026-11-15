from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

ProgrammeKind = Literal["talent", "teacher", "volunteer"]

class Study(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Optional[str] = None
    level: Optional[str] = None
    field: Optional[str] = None


class Duration(BaseModel):
    model_config = ConfigDict(extra="allow")
    min_weeks: Optional[int] = Field(None, ge=0)
    max_weeks: Optional[int] = Field(None, ge=0)

    @model_validator(mode="after")
    def _min_not_above_max(self):
        if self.min_weeks is not None and self.max_weeks is not None and self.min_weeks > self.max_weeks:
            raise ValueError("min_weeks must not be greater than max_weeks")
        return self


class Financial(BaseModel):
    model_config = ConfigDict(extra="allow")
    willing_to_pay: Optional[bool] = None
    max_budget_eur: Optional[float] = Field(None, ge=0)


class ProfileSnapshot(BaseModel):
    model_config = ConfigDict(extra="allow")   # новые поля бэка не ломают нас
    programmes: List[ProgrammeKind] = []
    english_level: Optional[Literal["A1","A2","B1","B2","C1","C2"]] = None
    study: Optional[Study] = None
    work_experience: Optional[str] = None
    spheres: List[str] = []
    activities: List[str] = []
    desired_countries: List[str] = []
    duration: Optional[Duration] = None
    start_window: Optional[str] = None
    financial: Optional[Financial] = None
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