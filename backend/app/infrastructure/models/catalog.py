from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, Integer, Numeric, String, MetaData,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CatalogBase(DeclarativeBase):
    metadata = MetaData(schema="catalog")


class OpportunityV1(CatalogBase):
    __tablename__ = "opportunity_v1"
    opportunity_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    family_key: Mapped[str | None] = mapped_column(String(120))
    programme_id: Mapped[int] = mapped_column(Integer)
    programme_kind: Mapped[str] = mapped_column(String(16))
    country_code: Mapped[str] = mapped_column(String(2))
    country_name: Mapped[str] = mapped_column(String(100))
    lc_id: Mapped[int] = mapped_column(Integer)
    lc_name: Mapped[str | None] = mapped_column(String(120))
    location: Mapped[str | None] = mapped_column(String(200))
    organisation_id: Mapped[int | None] = mapped_column(Integer)
    organisation_name: Mapped[str | None] = mapped_column(String(200))
    openings: Mapped[int | None] = mapped_column(Integer)
    available_openings: Mapped[int | None] = mapped_column(Integer)
    applicants_count: Mapped[int | None] = mapped_column(Integer)
    accepted_count: Mapped[int | None] = mapped_column(Integer)
    date_opened: Mapped[date | None] = mapped_column(Date)
    applications_close_date: Mapped[date | None] = mapped_column(Date)
    earliest_start_date: Mapped[date | None] = mapped_column(Date)
    latest_end_date: Mapped[date | None] = mapped_column(Date)
    duration_weeks: Mapped[int | None] = mapped_column(Integer)
    experience_type: Mapped[str | None] = mapped_column(String(40))
    cost_total: Mapped[Decimal | None] = mapped_column(Numeric)
    cost_currency: Mapped[str | None] = mapped_column(String(3))
    is_open: Mapped[bool] = mapped_column(Boolean)
    close_reason: Mapped[str | None] = mapped_column(String(120))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    remote_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OpportunityRequirementV1(CatalogBase):
    __tablename__ = "opportunity_requirement_v1"
    opportunity_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), primary_key=True)
    constant_id: Mapped[int | None] = mapped_column(Integer, primary_key=True)
    constant_name: Mapped[str | None] = mapped_column(String(200))
    parent_name: Mapped[str | None] = mapped_column(String(200))
    option: Mapped[str | None] = mapped_column(String(200))
    level: Mapped[str | None] = mapped_column(String(40))


class SyncStateV1(CatalogBase):
    __tablename__ = "sync_state_v1"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    committed_watermark: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))