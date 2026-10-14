"""Логика синхронизации.

full         — полный проход по целевым странам/городам, всё, чего нет в выдаче open, закрываем.
incremental  — только новые стажировки (фильтр по дате created.from), дёшево, часто.
reconcile    — лёгкая сверка статусов: тянем только id/status/места/дедлайн по всем open целям,
               обновляем известные, закрываем пропавшие, новых догружаем (по id или полным проходом).
expire       — локально, без обращений к API: закрываем стажировки с прошедшим дедлайном.
"""
from __future__ import annotations

import logging
import threading
from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker

from .client import AiesecClient, AiesecError, AuthError, NotSupported
from .config import Settings, Targets
from .models import Opportunity, SyncRun, SyncState, utcnow
from .normalize import normalize

log = logging.getLogger("aiesec.sync")


class SyncService:
    def __init__(self, client: AiesecClient, settings: Settings, targets: Targets, session_factory: sessionmaker):
        self.client = client
        self.settings = settings
        self.targets = targets
        self.Session = session_factory
        self._lock = threading.Lock()

    # ---------- запуск ----------
    def is_running(self) -> bool:
        return self._lock.locked()

    def try_start(self, kind: str) -> int | None:
        """Занимает блокировку и создаёт запись о запуске. None — синхронизация уже идёт."""
        if not self._lock.acquire(blocking=False):
            return None
        try:
            with self.Session() as s:
                run = SyncRun(kind=kind)
                s.add(run)
                s.commit()
                return run.run_id
        except Exception:
            self._lock.release()
            raise

    def execute(self, run_id: int, kind: str) -> None:
        stats: Counter = Counter()
        status, error = "ok", None
        try:
            {"full": self._full, "incremental": self._incremental, "reconcile": self._reconcile}[kind](stats)
        except AuthError as e:
            log.error("AIESEC отклонил токен: %s", e)
            status, error = "auth_failed", f"AuthError: {e}"[:2000]
        except Exception as e:  # noqa: BLE001
            log.exception("sync %s упал", kind)
            status, error = "failed", f"{type(e).__name__}: {e}"[:2000]
        finally:
            with self.Session() as s:
                run = s.get(SyncRun, run_id)
                run.status, run.error, run.stats, run.finished_at = status, error, dict(stats), utcnow()
                s.commit()
            self._lock.release()

    def run_now(self, kind: str) -> None:
        """Для планировщика: пропускаем запуск, если уже что-то выполняется или токен заведомо мёртв
        (долбить AIESEC заведомо неверным токеном — прямой путь к блокировке)."""
        if getattr(self.client, "auth_ok", None) is False:
            log.warning("sync %s пропущен: токен AIESEC отклонён. Обновите его: PUT /admin/token", kind)
            return
        run_id = self.try_start(kind)
        if run_id is None:
            log.info("sync %s пропущен: уже выполняется другой", kind)
            return
        self.execute(run_id, kind)

    # ---------- состояние ----------
    def get_state(self, key: str) -> str | None:
        with self.Session() as s:
            row = s.get(SyncState, key)
            return row.value if row else None

    def set_state(self, key: str, value: str) -> None:
        with self.Session() as s:
            s.merge(SyncState(key=key, value=value))
            s.commit()

    def has_bootstrapped(self) -> bool:
        return self.get_state("last_full_at") is not None

    # ---------- построение запросов ----------
    def _queries(self, extra: dict | None = None) -> list[tuple[str, dict]]:
        known = self.client.schema().filters
        out = []
        for name, geo in self.targets.geo_queries():
            bad_geo = [k for k in geo if k not in known]
            if bad_geo:
                raise AiesecError(f"Схема не поддерживает гео-фильтры {bad_geo}")
            filters = {**self.targets.base_filters, **(extra or {}), **geo}
            for k in [k for k in filters if k not in known]:
                log.warning("фильтр '%s' не поддерживается схемой — отбрасываю", k)
                filters.pop(k)
            out.append((name, filters))
        if not out:
            raise AiesecError("В targets.json нет ни стран, ни городов")
        return out

    # ---------- актуальность ----------
    def _actuality(self, d: dict, today: date, check_target: bool) -> tuple[bool, str | None]:
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

    # ---------- upsert ----------
    def _ingest_one(self, s, raw: dict, source: str, full: bool, today: date, now: datetime) -> str:
        d = normalize(raw, full=full)
        ok, reason = self._actuality(d, today, check_target=full)
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

    def _ingest(self, s, rows: list[dict], source: str, stats: Counter, seen: set[int], full: bool) -> None:
        today, now = date.today(), utcnow()
        for raw in rows:
            seen.add(int(raw["id"]))
            stats[self._ingest_one(s, raw, source, full, today, now)] += 1
        s.commit()

    def _close_missing(self, s, seen: set[int], stats: Counter, reason: str = "not_in_open_list") -> None:
        """Всё, что у нас open, но не пришло в полной выдаче open, — закрываем (с предохранителем)."""
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
            s.execute(update(Opportunity)
                      .where(Opportunity.opportunity_id.in_(ids[i:i + 500]))
                      .values(is_open=False, close_reason=reason, closed_at=now, updated_at=now))
        s.commit()
        stats["closed"] += len(missing)

    # ---------- режимы ----------
    def _full(self, stats: Counter) -> None:
        started = utcnow()
        seen: set[int] = set()
        with self.Session() as s:
            for name, filters in self._queries():
                log.info("full → %s: %s", name, filters)
                for rows in self.client.iter_pages(filters, "full"):
                    self._ingest(s, rows, name, stats, seen, full=True)
            stats["fetched"] = len(seen)
            self._close_missing(s, seen, stats)
        self.set_state("last_full_at", started.isoformat())
        self.set_state("last_incremental_at", started.isoformat())

    def _incremental(self, stats: Counter) -> None:
        started = utcnow()
        df = self.settings.incremental_date_filter
        anchor = self.get_state("last_incremental_at") or self.get_state("last_full_at")
        if not anchor:
            stats["fallback"] = "full (первого полного прохода ещё не было)"
            return self._full(stats)
        if not self.client.supports_range_filter(df):
            log.warning("фильтр '%s' {from,to} не поддерживается — делаю full", df)
            stats["fallback"] = f"full (нет фильтра {df})"
            return self._full(stats)

        since = (datetime.fromisoformat(anchor) - timedelta(days=self.settings.incremental_overlap_days)).date()
        stats["since"] = since.isoformat()
        seen: set[int] = set()
        with self.Session() as s:
            for name, filters in self._queries({df: {"from": since.isoformat()}}):
                log.info("incremental → %s: %s", name, filters)
                for rows in self.client.iter_pages(filters, "full"):
                    self._ingest(s, rows, name, stats, seen, full=True)
        stats["fetched"] = len(seen)
        self.set_state("last_incremental_at", started.isoformat())

    def _reconcile(self, stats: Counter) -> None:
        started = utcnow()
        with self.Session() as s:
            known_ids = set(s.scalars(select(Opportunity.opportunity_id)))
            has_open = s.scalar(select(Opportunity.opportunity_id).where(Opportunity.is_open.is_(True)).limit(1))
        if not has_open:
            stats["fallback"] = "full (в базе нет открытых)"
            return self._full(stats)

        seen: set[int] = set()
        new_ids: set[int] = set()
        today = date.today()
        with self.Session() as s:
            for name, filters in self._queries():
                log.info("reconcile → %s: %s", name, filters)
                for rows in self.client.iter_pages(filters, "slim"):
                    known_rows = []
                    for r in rows:
                        oid = int(r["id"])
                        seen.add(oid)
                        if oid in known_ids:
                            known_rows.append(r)
                        elif self._actuality(normalize(r, full=False), today, check_target=False)[0]:
                            new_ids.add(oid)
                    self._ingest(s, known_rows, name, stats, set(), full=False)
            stats["remote_open"] = len(seen)
            self._close_missing(s, seen, stats)
        stats["new_found"] = len(new_ids)

        if new_ids:  # incremental что-то упустил — догружаем полные данные
            self._gap_fill(new_ids, stats)
        self.set_state("last_reconcile_at", started.isoformat())

    def _gap_fill(self, ids: set[int], stats: Counter) -> None:
        if len(ids) <= self.settings.gap_fill_max:
            try:
                with self.Session() as s:
                    for oid in ids:
                        raw = self.client.get_opportunity(oid)
                        if raw:
                            self._ingest(s, [raw], "gap_fill", stats, set(), full=True)
                stats["gap_fill"] = "by_id"
                return
            except NotSupported:
                log.warning("opportunity(id) недоступен — догружаю полным проходом")
        stats["gap_fill"] = "full_scan"
        self._full(stats)

    # ---------- вне блокировки ----------
    def expire_by_deadline(self) -> int:
        """Локально, без API: закрываем всё, у чего прошёл дедлайн приёма заявок."""
        now = utcnow()
        with self.Session() as s:
            res = s.execute(update(Opportunity)
                            .where(Opportunity.is_open.is_(True),
                                   Opportunity.applications_close_date.is_not(None),
                                   Opportunity.applications_close_date < date.today())
                            .values(is_open=False, close_reason="deadline_passed", closed_at=now, updated_at=now))
            s.commit()
            if res.rowcount:
                log.info("закрыто по дедлайну: %s", res.rowcount)
            return res.rowcount or 0

    def refresh_one(self, opportunity_id: int) -> dict:
        """Точечная проверка одной стажировки по id (1 запрос к AIESEC)."""
        raw = self.client.get_opportunity(opportunity_id)  # NotSupported пробросится наверх
        if raw is None:
            return {"result": "not_found_remote"}
        with self.Session() as s:
            result = self._ingest_one(s, raw, "refresh", True, date.today(), utcnow())
            s.commit()
        return {"result": result}