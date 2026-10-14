from __future__ import annotations

import os
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Opportunity(Base):
    __tablename__ = "opportunities"

    # --- идентификатор: id стажировки в AIESEC ---
    opportunity_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)

    title: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(50))
    current_status: Mapped[str | None] = mapped_column(String(50))
    programme_id: Mapped[int | None] = mapped_column(Integer, index=True)
    programme_name: Mapped[str | None] = mapped_column(String(100))

    home_mc_id: Mapped[int | None] = mapped_column(Integer, index=True)
    home_mc_name: Mapped[str | None] = mapped_column(String(200))
    home_lc_id: Mapped[int | None] = mapped_column(Integer, index=True)
    home_lc_name: Mapped[str | None] = mapped_column(String(200))
    host_lc_id: Mapped[int | None] = mapped_column(Integer, index=True)
    host_lc_name: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(300))
    organisation_id: Mapped[int | None] = mapped_column(Integer)
    organisation_name: Mapped[str | None] = mapped_column(String(300))

    openings: Mapped[int | None] = mapped_column(Integer)
    available_openings: Mapped[int | None] = mapped_column(Integer)
    applicants_count: Mapped[int | None] = mapped_column(Integer)
    accepted_count: Mapped[int | None] = mapped_column(Integer)

    date_opened: Mapped[date | None] = mapped_column(Date)
    applications_close_date: Mapped[date | None] = mapped_column(Date, index=True)
    earliest_start_date: Mapped[date | None] = mapped_column(Date)
    latest_end_date: Mapped[date | None] = mapped_column(Date)
    duration: Mapped[int | None] = mapped_column(Integer)
    experience_type: Mapped[str | None] = mapped_column(String(100))
    cost_total: Mapped[float | None] = mapped_column(Float)
    cost_currency: Mapped[str | None] = mapped_column(String(10))
    remote_updated_at: Mapped[str | None] = mapped_column(String(50))

    skills: Mapped[list | None] = mapped_column(JSON)
    backgrounds: Mapped[list | None] = mapped_column(JSON)
    languages: Mapped[list | None] = mapped_column(JSON)
    study_levels: Mapped[list | None] = mapped_column(JSON)
    nationalities: Mapped[list | None] = mapped_column(JSON)
    skills_developments: Mapped[list | None] = mapped_column(JSON)
    raw: Mapped[dict | None] = mapped_column(JSON)  # полный ответ API

    # --- наша служебная часть ---
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    close_reason: Mapped[str | None] = mapped_column(String(50))
    source_query: Mapped[str | None] = mapped_column(String(50))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SyncRun(Base):
    __tablename__ = "sync_runs"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(20))  # full | incremental | reconcile
    status: Mapped[str] = mapped_column(String(20), default="running")  # running | ok | failed
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    stats: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)


class SyncState(Base):
    __tablename__ = "sync_state"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text)


def make_session_factory(url: str) -> sessionmaker:
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        path = url.split("///", 1)[-1]
        if path and os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
    engine = create_engine(url, pool_pre_ping=True, **kwargs)
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)
