from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.domain.models import Opportunity

log = logging.getLogger("matcher.catalog")

KIND_TO_FIELD = {"background": "backgrounds", "skill": "skills", "language": "languages"}


def _d(v) -> Optional[date]:
    if v is None or isinstance(v, date):
        return v
    return date.fromisoformat(str(v)[:10])


def build_opportunity(row: dict, reqs: List[dict]) -> Opportunity:
    """Строка вью opportunity_v1 + её строки из opportunity_requirement_v1 -> Opportunity."""
    opp = Opportunity(
        opportunity_id=int(row["opportunity_id"]),
        programme_kind=row["programme_kind"],
        title=row.get("title") or "",
        family_key=row.get("family_key"),
        country_code=row.get("country_code"),
        lc_id=row.get("lc_id"),
        is_open=bool(row.get("is_open", True)),
        openings=row.get("openings") or 0,
        available_openings=row.get("available_openings") or 0,
        applicants_count=row.get("applicants_count") or 0,
        accepted_count=row.get("accepted_count") or 0,
        date_opened=_d(row.get("date_opened")),
        applications_close_date=_d(row.get("applications_close_date")),
        duration_weeks=row.get("duration_weeks"),
        cost_total=float(row["cost_total"]) if row.get("cost_total") is not None else None,
        cost_currency=row.get("cost_currency"),
    )
    for r in reqs:
        cid = int(r["constant_id"])
        kind = r["kind"]
        if kind in KIND_TO_FIELD:
            getattr(opp, KIND_TO_FIELD[kind])[cid] = r.get("option") or "required"
        elif kind == "study_level":
            opp.study_levels.add(cid)
        elif kind == "nationality":
            opp.nationalities.add(cid)
    return opp


class FakeCatalogReader:
    """Вакансии из JSON-файла: для разработки и тестов."""

    def __init__(self, path: str):
        resolved = Path(path)
        if not resolved.is_absolute():
            # app/repo/catalog_reader.py -> parents[2] == корень проекта
            resolved = Path(__file__).resolve().parents[2] / path
        with resolved.open(encoding="utf-8") as f:
            data = json.load(f)
        self._all = [build_opportunity(o, o.get("requirements", [])) for o in data]

    def list_open(self, programme_kind: str) -> List[Opportunity]:
        return [
            o for o in self._all
            if o.programme_kind == programme_kind and o.is_open and o.available_openings > 0
        ]


class DbCatalogReader:
    """Чтение из вью catalog.* под ролью только для SELECT."""

    def __init__(
        self,
        database_url: str,
        *,
        pool_size: int = 20,
        max_overflow: int = 10,
    ):
        # Драйвер должен совпадать с тем, что установлен в образе (psycopg[binary]).
        # SQLAlchemy 2.x по умолчанию выбирает psycopg.
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace(
                "postgresql+asyncpg://", "postgresql+psycopg://", 1,
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1,
            )
        self._engine: Engine = create_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            future=True,
        )

    def list_open(self, programme_kind: str) -> List[Opportunity]:
        with self._engine.connect() as conn:
            # Явная read-only транзакция: SET TRANSACTION действует только
            # внутри уже начатой транзакции.
            with conn.begin():
                conn.execute(text("SET TRANSACTION READ ONLY"))
                rows = conn.execute(
                    text("""
                        SELECT * FROM catalog.opportunity_v1
                        WHERE programme_kind = :k AND is_open AND available_openings > 0
                        ORDER BY opportunity_id
                    """),
                    {"k": programme_kind},
                ).mappings().all()

                ids = [r["opportunity_id"] for r in rows]
                reqs: Dict[int, List[dict]] = {i: [] for i in ids}
                if ids:
                    for r in conn.execute(
                        text("""
                            SELECT opportunity_id, kind, constant_id, option
                            FROM catalog.opportunity_requirement_v1
                            WHERE opportunity_id = ANY(:ids)
                            ORDER BY opportunity_id, kind, constant_id
                        """),
                        {"ids": ids},
                    ).mappings():
                        reqs[r["opportunity_id"]].append(dict(r))

        return [build_opportunity(dict(r), reqs[r["opportunity_id"]]) for r in rows]