from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, EmailStr, Field

ProgrammeKind = Literal["talent", "teacher", "volunteer"]


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AnonymousAuthIn(BaseModel):
    device_secret: str | None = None


class AnonymousAuthOut(BaseModel):
    access_token: str
    expires_in: int
    device_secret: str | None = None


class TokenOut(BaseModel):
    access_token: str
    expires_in: int
    is_anonymous: bool = False


class TelegramAuthIn(BaseModel):
    init_data: str


class MeOut(BaseModel):
    user_id: str
    is_anonymous: bool
    email: str | None = None
    has_profile: bool
    profile_version: int | None
    identities: list[dict]
    consents: list[dict]


class ConsentIn(BaseModel):
    kind: Literal["pd_processing", "marketing"]
    version: str


class FormSchemaOut(BaseModel):
    version: str
    steps: list[dict[str, Any]]


class ProfileIn(BaseModel):
    programmes: list[ProgrammeKind] = []
    birth_date: date | None = None
    city: str | None = Field(default=None, max_length=100)
    preferred_lc_ids: list[int] | None = None
    study: dict[str, Any] | None = None
    english_level: Literal["A1","A2","B1","B2","C1","C2"] | None = None
    other_languages: list[str] | None = None
    work_experience: Literal["none","1_2_years","3_5_years","5_plus_years"] | None = None
    spheres: list[str] | None = None
    activities: list[str] | None = None
    desired_countries: list[str] | None = None
    duration: dict[str, int] | None = None
    start_window: str | None = None
    financial: dict[str, Any] | None = None
    abroad_experience: bool | None = None
    nationality: str | None = None
    experience_text: str | None = Field(default=None, max_length=2000)
    motivation_text: str | None = Field(default=None, max_length=1000)


class ProfileOut(ProfileIn):
    profile_version: int
    age_years: int | None
    completeness: float
    updated_at: datetime


class ProfileVersionEntry(BaseModel):
    version: int
    created_at: datetime
    completeness: float


class ProfileVersionSnapshot(ProfileOut):
    version: int
    created_at: datetime


class OpportunityCard(BaseModel):
    opportunity_id: int
    title: str
    family_key: str | None
    programme: dict[str, Any]
    place: dict[str, Any]
    organisation_name: str | None
    capacity: dict[str, int]
    duration_weeks: int | None
    cost: dict[str, Any] | None
    requirements: list[dict[str, Any]] = []
    date_opened: date | None
    applications_close_date: date | None
    is_open: bool
    updated_at: datetime


class Page(BaseModel):
    items: list[Any]
    total: int
    limit: int
    offset: int


class RecommendationRunIn(BaseModel):
    filters: dict[str, Any] | None = None
    limit_per_programme: int = Field(10, ge=1, le=30)
    mode: Literal["sync", "async"] = "sync"
    strategy: str | None = None


class RecItem(BaseModel):
    rank: int
    score: float
    label: Literal["excellent", "good", "fair"]
    family: dict[str, Any]
    opportunity: OpportunityCard
    reasons: list[dict[str, Any]]


class RecGroup(BaseModel):
    programme_kind: ProgrammeKind
    total_candidates: int
    items: list[RecItem]


class RecommendationRun(BaseModel):
    run_id: str
    state: Literal["queued","running","succeeded","failed"]
    profile_version: int
    strategy: str | None
    created_at: datetime
    finished_at: datetime | None
    catalog_watermark: datetime | None
    programme_prior: list[str]
    degraded: bool = False
    groups: list[RecGroup] = []
    error: str | None = None


class FeedbackIn(BaseModel):
    opportunity_id: int
    signal: Literal["opened","liked","disliked","hidden","applied"]
    run_id: str | None = None


class SubscriptionPrefs(BaseModel):
    notify_new_matches: bool = True
    min_score: float = Field(0.7, ge=0, le=1)
    channels: list[Literal["telegram"]] = ["telegram"]