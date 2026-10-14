"""Приведение ответа AIESEC к колонкам БД. Возвращает только те колонки, чьи поля реально пришли
(важно для «лёгких» запросов сверки: они не должны затирать остальные поля None-ами)."""
from __future__ import annotations

from datetime import date
from typing import Any

_MISSING = object()

# колонка -> поле верхнего уровня в API
SCALARS = {
    "title": "title",
    "status": "status",
    "current_status": "current_status",
    "location": "location",
    "openings": "openings",
    "available_openings": "available_openings",
    "applicants_count": "applicants_count",
    "accepted_count": "accepted_count",
    "duration": "duration",
    "experience_type": "experience_type",
    "remote_updated_at": "updated_at",
    "date_opened": "date_opened",
    "applications_close_date": "applications_close_date",
    "earliest_start_date": "earliest_start_date",
    "latest_end_date": "latest_end_date",
    "skills": "skills",
    "backgrounds": "backgrounds",
    "languages": "languages",
    "study_levels": "study_levels",
    "nationalities": "nationalities",
    "skills_developments": "skills_developments",
}

# колонка -> варианты пути во вложенных объектах (берём первый непустой)
NESTED = {
    "programme_id": [("programme", "id")],
    "programme_name": [("programme", "short_name_display"), ("programme", "short_name"), ("programme", "name")],
    "home_mc_id": [("home_mc", "id")],
    "home_mc_name": [("home_mc", "name"), ("home_mc", "full_name")],
    "home_lc_id": [("home_lc", "id")],
    "home_lc_name": [("home_lc", "name"), ("home_lc", "full_name")],
    "host_lc_id": [("host_lc", "id")],
    "host_lc_name": [("host_lc", "name"), ("host_lc", "full_name")],
    "organisation_id": [("organisation", "id")],
    "organisation_name": [("organisation", "name")],
    "cost_total": [("opportunity_cost", "total")],
    "cost_currency": [("opportunity_cost", "currency")],
}

INT_COLS = {"programme_id", "home_mc_id", "home_lc_id", "host_lc_id", "organisation_id",
            "openings", "available_openings", "applicants_count", "accepted_count", "duration"}
DATE_COLS = {"date_opened", "applications_close_date", "earliest_start_date", "latest_end_date"}


def to_int(v: Any) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def to_float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def to_date(v: Any) -> date | None:
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _dig(raw: dict, path: tuple[str, ...]) -> Any:
    cur: Any = raw
    for i, k in enumerate(path):
        if not isinstance(cur, dict) or k not in cur:
            return None if (i > 0 and cur is None) else _MISSING
        cur = cur[k]
    return cur


def normalize(raw: dict, full: bool = True) -> dict:
    out: dict[str, Any] = {"opportunity_id": int(raw["id"])}
    for col, key in SCALARS.items():
        if key in raw:
            out[col] = raw[key]
    for col, paths in NESTED.items():
        vals = [_dig(raw, p) for p in paths]
        present = [v for v in vals if v is not _MISSING]
        if present:
            out[col] = next((v for v in present if v not in (None, "")), None)
    for col in INT_COLS & out.keys():
        out[col] = to_int(out[col])
    for col in DATE_COLS & out.keys():
        out[col] = to_date(out[col])
    if "cost_total" in out:
        out["cost_total"] = to_float(out["cost_total"])
    if full:
        out["raw"] = raw
    return out
