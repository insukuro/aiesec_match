"""Публичный фасад SyncService. Сохраняет прежний API для API-слоя и тестов."""
from __future__ import annotations

import logging
import threading
from collections import Counter
from datetime import date

from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from ..client import AiesecClient, AuthError
from ..config import Settings, Targets
from ..models import Opportunity, SyncRun, utcnow
from .ingest import Ingestor
from .state import StateStore
from .strategies import FullStrategy, IncrementalStrategy, ReconcileStrategy

log = logging.getLogger("aiesec.sync")


class SyncService:
    def __init__(self, client: AiesecClient, settings: Settings, targets: Targets,
                 session_factory: sessionmaker):
        self.client = client
        self.settings = settings
        self.targets = targets
        self.Session = session_factory
        self.state = StateStore(session_factory)
        self.ingestor = Ingestor(settings, targets, session_factory)
        full = FullStrategy(client, settings, targets, self.ingestor, self.state)
        incremental = IncrementalStrategy(client, settings, targets, self.ingestor, self.state, full)
        reconcile = ReconcileStrategy(client, settings, targets, self.ingestor, self.state, full)
        self._strategies = {"full": full, "incremental": incremental, "reconcile": reconcile}
        self._lock = threading.Lock()

    # ---------- запуск ----------
    def is_running(self) -> bool:
        return self._lock.locked()

    def try_start(self, kind: str) -> int | None:
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
            self._strategies[kind].run(stats)
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
        if getattr(self.client, "auth_ok", None) is False:
            log.warning("sync %s пропущен: токен AIESEC отклонён. Обновите его: PUT /admin/token", kind)
            return
        run_id = self.try_start(kind)
        if run_id is None:
            log.info("sync %s пропущен: уже выполняется другой", kind)
            return
        self.execute(run_id, kind)

    def run_sync_for_test(self, kind: str) -> None:
        """Публичный запуск стратегии без блокировки. Только для тестов и ручного дерганья."""
        self._strategies[kind].run(Counter())

    # ---------- состояние ----------
    def get_state(self, key: str) -> str | None:
        return self.state.get(key)

    def set_state(self, key: str, value: str) -> None:
        self.state.set(key, value)

    def set_states(self, items: dict[str, str]) -> None:
        self.state.set_many(items)

    def has_bootstrapped(self) -> bool:
        return self.get_state("last_full_at") is not None

    # ---------- вне блокировки ----------
    def expire_by_deadline(self) -> int:
        now = utcnow()
        with self.Session() as s:
            res = s.execute(
                update(Opportunity)
                .where(
                    Opportunity.is_open.is_(True),
                    Opportunity.applications_close_date.is_not(None),
                    Opportunity.applications_close_date < date.today(),
                )
                .values(is_open=False, close_reason="deadline_passed", closed_at=now, updated_at=now)
            )
            s.commit()
            if res.rowcount:
                log.info("закрыто по дедлайну: %s", res.rowcount)
            return res.rowcount or 0

    def refresh_one(self, opportunity_id: int) -> dict:
        raw = self.client.get_opportunity(opportunity_id)  # NotSupported пробросится наверх
        if raw is None:
            return {"result": "not_found_remote"}
        with self.Session() as s:
            result = self.ingestor.upsert_one(s, raw, "refresh", True, date.today(), utcnow())
            s.commit()
        return {"result": result}