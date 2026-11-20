from datetime import date, datetime
import re
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from .domain.age import validate_birth_date

ProgrammeKind = Literal["talent", "teacher", "volunteer"]
ConsentKind = Literal["pd_processing", "marketing"]

_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


def _validate_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("password_too_short")
    if len(v) > 128:
        raise ValueError("password_too_long")
    if not _PASSWORD_RE.match(v):
        raise ValueError("password_weak")
    return v


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str) -> str:
        return v.strip().lower()


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str) -> str:
        return v.strip().lower()


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password(cls, v: str) -> str:
        return _validate_password(v)


class ChangeEmailIn(BaseModel):
    new_email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("new_email")
    @classmethod
    def _email_lower(cls, v: str) -> str:
        return v.strip().lower()


class VerifyEmailIn(BaseModel):
    code: str = Field(min_length=4, max_length=12)


class TokenOut(BaseModel):
    access_token: str
    expires_in: int


class TelegramAuthIn(BaseModel):
    init_data: str


class ConsentAcceptanceOut(BaseModel):
    kind: ConsentKind
    version: str
    accepted_at: datetime


class MeOut(BaseModel):
    user_id: str
    email: str | None = None
    email_verified: bool = False
    has_profile: bool
    profile_version: int | None
    identities: list[dict]
    consents: list[ConsentAcceptanceOut]


class ConsentIn(BaseModel):
    kind: ConsentKind
    version: str


class ConsentDocumentOut(BaseModel):
    kind: ConsentKind
    version: str
    title: str
    text: str
    label: str
    required: bool


class ConsentSchemaOut(BaseModel):
    version: str
    consents: list[ConsentDocumentOut]


class FormSchemaOut(BaseModel):
    version: str
    steps: list[dict[str, Any]]


class ProfileIn(BaseModel):
    programmes: list[ProgrammeKind] = []
    birth_date: date | None = None
    city: str | None = Field(default=None, max_length=100)
    preferred_lc_ids: list[int] | None = None
    study: dict[str, Any] | None = None
    english_level: Literal["A1", "A2", "B1", "B2", "C1", "C2"] | None = None
    other_languages: list[str] | None = None
    work_experience: Literal["none", "1_2_years", "3_5_years", "5_plus_years"] | None = None
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

    @field_validator("birth_date")
    @classmethod
    def _check_age(cls, v: date | None) -> date | None:
        try:
            validate_birth_date(v)
        except ValueError as e:
            raise ValueError(str(e)) from e
        return v


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


class RecommendationRunSummary(BaseModel):
    run_id: str
    state: Literal["queued", "running", "succeeded", "failed"]
    profile_version: int
    total_candidates: int | None
    created_at: datetime
    finished_at: datetime | None
    error: str | None = None


class RecItem(BaseModel):
    rank: int
    score: float
    label: Literal["excellent", "good", "fair"]
    family: dict[str, Any]
    opportunity: OpportunityCard
    reasons: list[dict[str, Any]]
    liked: bool = False
    hidden: bool = False


class RecGroup(BaseModel):
    programme_kind: ProgrammeKind
    total_candidates: int
    items: list[RecItem]


class RecommendationRun(BaseModel):
    run_id: str
    state: Literal["queued", "running", "succeeded", "failed"]
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
    signal: Literal["opened", "liked", "disliked", "hidden", "applied"]
    run_id: str | None = None


class SubscriptionPrefs(BaseModel):
    notify_new_matches: bool = True
    min_score: float = Field(0.7, ge=0, le=1)
    channels: list[Literal["telegram"]] = ["telegram"]


class AnalyticsOut(BaseModel):
    profile_completeness: dict[str, Any]
    programme_distribution: list[dict[str, Any]]
    interests_distribution: list[dict[str, Any]]
    activity_series: list[dict[str, Any]]
    recommendation_statistics: list[dict[str, Any]]


class NotificationItem(BaseModel):
    notification_id: str
    kind: str
    payload: dict[str, Any]
    created_at: datetime
    sent_at: datetime | None
    read_at: datetime | None


class NotificationsPage(BaseModel):
    items: list[NotificationItem]
    total: int
    limit: int
    offset: int
    unread: int


class LinkCodeOut(BaseModel):
    code: str
    expires_in: int
