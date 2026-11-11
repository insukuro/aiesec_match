from __future__ import annotations
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric,
    String, Text, UniqueConstraint, func, text, MetaData
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    metadata = MetaData(schema="core")


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Identity(Base):
    __tablename__ = "identities"
    identity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(20))          # anonymous | telegram
    external_id: Mapped[str | None] = mapped_column(String(120))
    __table_args__ = (UniqueConstraint("provider", "external_id"),)


class DeviceSecret(Base):
    __tablename__ = "device_secrets"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    secret_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Consent(Base):
    __tablename__ = "consents"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    current_version: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProfileVersion(Base):
    __tablename__ = "profile_versions"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[dict[str, Any]] = mapped_column(JSONB)
    birth_date: Mapped[date | None] = mapped_column(Date)
    completeness: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    profile_version: Mapped[int] = mapped_column(Integer)
    strategy: Mapped[str | None] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(16), default="queued")
    filters: Mapped[dict] = mapped_column(JSONB, default=dict)
    programme_prior: Mapped[list | None] = mapped_column(JSONB)
    model_versions: Mapped[dict | None] = mapped_column(JSONB)
    catalog_watermark: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_candidates: Mapped[int | None] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        Index("ix_runs_user_created", "user_id", text("created_at DESC")),
    )


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recommendation_runs.run_id", ondelete="CASCADE"), primary_key=True)
    programme_kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    rank: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(Integer)
    family_key: Mapped[str | None] = mapped_column(String(120))
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    reasons: Mapped[list] = mapped_column(JSONB, default=list)


class Feedback(Base):
    __tablename__ = "feedback"
    feedback_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    opportunity_id: Mapped[int] = mapped_column(Integer)
    signal: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index("uq_feedback_sig", "user_id", "opportunity_id", "signal", "run_id", unique=True,
              postgresql_nulls_not_distinct=True),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    notify_new_matches: Mapped[bool] = mapped_column(default=True)
    min_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal("0.700"))
    channels: Mapped[list[str]] = mapped_column(ARRAY(String(16)), default=lambda: ["telegram"])
    last_notified_watermark: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"
    notification_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    telegram_chat_id: Mapped[int | None]
    kind: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSONB)
    state: Mapped[str] = mapped_column(String(16), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dedupe_key: Mapped[str] = mapped_column(String(120), unique=True)
    __table_args__ = (Index("ix_outbox_state_lease", "state", "locked_until"),)


class LinkCode(Base):
    __tablename__ = "link_codes"
    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))