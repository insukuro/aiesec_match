"""Три стратегии синка: full, incremental, reconcile."""
from __future__ import annotations

import logging
from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy import select

from ..client import AiesecClient, AiesecError
from ..config import Settings, Targets
from ..models import Opportunity, utcnow
from ..normalize import normalize
from .gapfill import gap_fill
from .ingest import Ingestor
from .queries import build_queries
from .state import StateStore

log = logging.getLogger("aiesec.sync.strategies")


class FullStrategy:
    def __init__(self, client: AiesecClient, settings: Settings, targets: Targets,
                 ingestor: Ingestor, state: StateStore):
        self.client, self.settings, self.targets = client, settings, targets
        self.ingestor, self.state = ingestor, state

    def run(self, stats: Counter) -> None:
        started = utcnow()
        seen: set[int] = set()
        with self.ingestor.Session() as s:
            for name, filters in build_queries(self.client, self.targets):
                log.info("full → %s: %s", name, filters)
                for rows in self.client.iter_pages(filters, "full"):
                    self.ingestor.ingest_page(s, rows, name, stats, seen, full=True)
            stats["fetched"] = len(seen)
            self.ingestor.close_missing(s, seen, stats)
        self.state.set("last_full_at", started.isoformat())
        self.state.set("last_incremental_at", started.isoformat())


class IncrementalStrategy:
    def __init__(self, client: AiesecClient, settings: Settings, targets: Targets,
                 ingestor: Ingestor, state: StateStore, full: FullStrategy):
        self.client, self.settings, self.targets = client, settings, targets
        self.ingestor, self.state, self.full = ingestor, state, full

    def run(self, stats: Counter) -> None:
        started = utcnow()
        df = self.settings.incremental_date_filter
        anchor = self.state.get("last_incremental_at") or self.state.get("last_full_at")
        if not anchor:
            stats["fallback"] = "full (первого полного прохода ещё не было)"
            return self.full.run(stats)
        if not self.client.supports_range_filter(df):
            log.warning("фильтр '%s' {from,to} не поддерживается — делаю full", df)
            stats["fallback"] = f"full (нет фильтра {df})"
            return self.full.run(stats)

        since = (datetime.fromisoformat(anchor) - timedelta(days=self.settings.incremental_overlap_days)).date()
        stats["since"] = since.isoformat()
        seen: set[int] = set()
        with self.ingestor.Session() as s:
            for name, filters in build_queries(self.client, self.targets, {df: {"from": since.isoformat()}}):
                log.info("incremental → %s: %s", name, filters)
                for rows in self.client.iter_pages(filters, "full"):
                    self.ingestor.ingest_page(s, rows, name, stats, seen, full=True)
        stats["fetched"] = len(seen)
        self.state.set("last_incremental_at", started.isoformat())


class ReconcileStrategy:
    def __init__(self, client: AiesecClient, settings: Settings, targets: Targets,
                 ingestor: Ingestor, state: StateStore, full: FullStrategy):
        self.client, self.settings, self.targets = client, settings, targets
        self.ingestor, self.state, self.full = ingestor, state, full

    def run(self, stats: Counter) -> None:
        started = utcnow()
        with self.ingestor.Session() as s:
            known_ids = set(s.scalars(select(Opportunity.opportunity_id)))
            has_open = s.scalar(
                select(Opportunity.opportunity_id).where(Opportunity.is_open.is_(True)).limit(1)
            )
        if not has_open:
            stats["fallback"] = "full (в базе нет открытых)"
            return self.full.run(stats)

        seen: set[int] = set()
        new_ids: set[int] = set()
        today = date.today()
        with self.ingestor.Session() as s:
            for name, filters in build_queries(self.client, self.targets):
                log.info("reconcile → %s: %s", name, filters)
                for rows in self.client.iter_pages(filters, "slim"):
                    known_rows = []
                    for r in rows:
                        oid = int(r["id"])
                        seen.add(oid)
                        if oid in known_ids:
                            known_rows.append(r)
                        elif self.ingestor.actuality(normalize(r, full=False), today, check_target=False)[0]:
                            new_ids.add(oid)
                    self.ingestor.ingest_page(s, known_rows, name, stats, set(), full=False)
            stats["remote_open"] = len(seen)
            self.ingestor.close_missing(s, seen, stats)
        stats["new_found"] = len(new_ids)

        if new_ids:
            gap_fill(self.client, self.ingestor, new_ids, stats, self.full.run)
        self.state.set("last_reconcile_at", started.isoformat())