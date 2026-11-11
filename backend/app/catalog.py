from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


CARD_SQL = text("""
SELECT opportunity_id, title, family_key,
       programme_id, programme_kind,
       country_code, country_name,
       lc_id, lc_name, location,
       organisation_id, organisation_name,
       openings, available_openings, applicants_count, accepted_count,
       date_opened, applications_close_date,
       earliest_start_date, latest_end_date,
       duration_weeks, experience_type,
       cost_total, cost_currency,
       is_open, close_reason,
       updated_at
FROM catalog.opportunity_v1
WHERE opportunity_id = ANY(:ids)
""")


async def fetch_cards(session: AsyncSession, ids: list[int]) -> dict[int, dict[str, Any]]:
    if not ids:
        return {}
    rows = (await session.execute(CARD_SQL, {"ids": ids})).mappings().all()
    return {r["opportunity_id"]: dict(r) for r in rows}


async def fetch_requirements(session: AsyncSession, ids: list[int]) -> dict[int, list[dict]]:
    if not ids:
        return {}
    rows = (await session.execute(text("""
        SELECT opportunity_id, kind, constant_id, constant_name, parent_name, option, level
        FROM catalog.opportunity_requirement_v1
        WHERE opportunity_id = ANY(:ids)
    """), {"ids": ids})).mappings().all()
    out: dict[int, list[dict]] = {}
    for r in rows:
        out.setdefault(r["opportunity_id"], []).append(dict(r))
    return out


async def list_opportunities(
    session: AsyncSession, *,
    q: str | None, programme_kind: str | None, country_code: str | None,
    lc_id: int | None, family_key: str | None, only_open: bool,
    sort: str, limit: int, offset: int,
) -> tuple[list[dict], int]:
    where = ["1=1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if q:
        where.append("title ILIKE :q"); params["q"] = f"%{q}%"
    if programme_kind:
        where.append("programme_kind = :pk"); params["pk"] = programme_kind
    if country_code:
        where.append("country_code = :cc"); params["cc"] = country_code
    if lc_id is not None:
        where.append("lc_id = :lc"); params["lc"] = lc_id
    if family_key:
        where.append("family_key = :fk"); params["fk"] = family_key
    if only_open:
        where.append("is_open AND available_openings > 0")

    order = {
        "new": "remote_updated_at DESC NULLS LAST, opportunity_id DESC",
        "closing": "applications_close_date ASC NULLS LAST, opportunity_id",
        "chance": "(available_openings::float / GREATEST(applicants_count,1)) DESC NULLS LAST",
    }[sort or "new"]

    base = " FROM catalog.opportunity_v1 WHERE " + " AND ".join(where)
    total = (await session.execute(text("SELECT count(*)" + base), params)).scalar_one()
    rows = (await session.execute(
        text(f"SELECT * {base} ORDER BY {order} LIMIT :limit OFFSET :offset"), params
    )).mappings().all()
    return [dict(r) for r in rows], int(total)


async def current_watermark(session: AsyncSession):
    row = (await session.execute(
        text("SELECT committed_watermark FROM catalog.sync_state_v1")
    )).scalar_one_or_none()
    return row