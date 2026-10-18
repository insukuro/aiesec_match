"""Upsert + actuality + close_missing. Единственный класс, который пишет в raw.opportunities."""
from __future__ import annotations

import logging
from collections import Counter
from datetime import date, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from ..client import AiesecError
from ..config import Settings, Targets
from ..models import Opportunity, utcnow
from ..normalize import normalize

log = logging.getLogger("aiesec.sync.ingest")


class Ingestor:
    def __init__(self, settings: Settings, targets: Targets, session_factory: sessionmaker):
        self.settings = settings
        self.targets = targets
        self.Session = session_factory

    def actuality(self, d: dict, today: date, check_target: bool) -> tuple[bool, str | None]:
        t = self.targets
        if check_target:
            in_country = d.get("home_mc_id") in t.mc_ids
            in_city = d.get("home_lc_id") in t.lc_ids or d.get("host_lc_id") in t.lc_ids
            if not (in_country or in_city):
                return False, "out_of_target"
        status = d.get("status")
        if status is not None and "open" not in str(status).lower():
            return False, "status_not_open"
        close = d.get("applications_close_date")
        if close and close < today:
            return False, "deadline_passed"
        slots = d.get("available_openings")
        if t.only_with_openings and isinstance(slots, (int, float)) and slots <= 0:
            return False, "no_openings"
        return True, None

    def upsert_one(
        self, s: Session, raw: dict, source: str, full: bool, today: date, now: datetime,
    ) -> str:
        d = normalize(raw, full=full)
        ok, reason = self.actuality(d, today, check_target=full)
        row = s.get(Opportunity, d["opportunity_id"])

        if row is None:
            if not ok:
                return f"skipped_{reason}"
            s.add(Opportunity(**d, is_open=True, source_query=source,
                              first_seen_at=now, last_seen_at=now, updated_at=now))
            return "inserted"

        was_open = row.is_open
        for k, v in d.items():
            setattr(row, k, v)
        row.last_seen_at = now
        row.updated_at = now
        if ok:
            row.is_open, row.close_reason, row.closed_at = True, None, None
            return "updated" if was_open else "reopened"
        if was_open:
            row.is_open, row.close_reason, row.closed_at = False, reason, now
            return "closed"
        row.close_reason = row.close_reason or reason
        return "still_closed"

    def ingest_page(
        self, s: Session, rows: list[dict], source: str,
        stats: Counter, seen: set[int], full: bool,
    ) -> None:
        today, now = date.today(), utcnow()
        for raw in rows:
            seen.add(int(raw["id"]))
            stats[self.upsert_one(s, raw, source, full, today, now)] += 1
        s.commit()

    def close_missing(
        self, s: Session, seen: set[int], stats: Counter, reason: str = "not_in_open_list",
    ) -> None:
        open_ids = set(s.scalars(select(Opportunity.opportunity_id).where(Opportunity.is_open.is_(True))))
        missing = open_ids - seen
        if not missing:
            return
        if len(open_ids) >= 20 and len(missing) / len(open_ids) > self.settings.max_close_ratio:
            raise AiesecError(
                f"Предохранитель: к закрытию {len(missing)} из {len(open_ids)} открытых "
                f"(> {self.settings.max_close_ratio:.0%}). Похоже на неполную выдачу, ничего не закрываю."
            )
        now = utcnow()
        ids = list(missing)
        for i in range(0, len(ids), 500):
            s.execute(
                update(Opportunity)
                .where(Opportunity.opportunity_id.in_(ids[i:i + 500]))
                .values(is_open=False, close_reason=reason, closed_at=now, updated_at=now)
            )
        s.commit()
        stats["closed"] += len(missing)