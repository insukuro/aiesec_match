"""Синтетические вакансии в том виде, как их хранит парсер (parser.opportunities).

Реальные данные AIESEC и персональные данные не используются: всё генерируется здесь.
Форма элементов требований скопирована с настоящей выдачи AIESEC:
у навыков, образования, языков и гражданства два разных числа:
  id          = номер строки-связки (например 178561793),
  constant_id = номер значения в справочнике (например 10161 = Sales).
У study_levels наоборот: справочный номер лежит в id, а название в name.
"""
from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta

# справочные значения (constant_id) из словарей AIESEC, которые знает матчер
BACKGROUNDS = [(10253, "Marketing"), (10233, "Business administration"), (21677, "Sales"), (10241, "Education")]
SKILLS = [(10161, "Sales"), (10159, "Presentation skills"), (11180, "Data Analysis"), (10162, "Teaching")]
LANGS = [(10018, "English"), (10043, "Russian"), (10048, "Spanish"), (10041, "Portuguese")]
NATIONS = [(10463, "Russia"), (10353, "Azerbaijan")]
STUDY = [(10782, "School"), (10785, "Bachelor")]
COUNTRIES = [(1622, "Turkiye", "TR"), (1559, "Tunisia", "TN"), (1609, "Egypt", "EG"), (1585, "India", "IN"),
             (504, "Vietnam", "VN"), (1589, "Mexico", "MX")]
PROGRAMMES = [(7, "GV"), (8, "GTa"), (9, "GTe")]
ROLES = ["Marketing Assistant", "Sales Intern", "English Teacher", "Data Analyst", "Event Volunteer",
         "HR Assistant", "Content Creator", "Eco Project Volunteer"]
COMPANIES = ["Northwind", "Blue Harbor", "Sunrise School", "Green Steps", "Orbit Labs", "Kite Studio"]

_link_id = 170_000_000


def _req(cid: int, name: str, option: str = "required", parent: str | None = None) -> dict:
    """Элемент требования в форме AIESEC: id строки-связки НЕ равен constant_id."""
    global _link_id
    _link_id += 1
    return {"id": str(_link_id), "level": None, "option": option, "position": None,
            "constant_id": cid, "parent_name": parent, "matches_with": None,
            "constant_name": name, "matching_with_opportunity": None}


def _study(cid: int, name: str) -> dict:
    return {"id": str(cid), "tag": None, "name": name, "option": None, "type_id": "study_level",
            "position": None, "is_active": True, "parent_id": 0, "type_name": "study_level"}


def make_row(oid: int, *, programme_id: int = 8, title: str | None = None, mc=(1622, "Turkiye", "TR"),
             lc_id: int = 2452, backgrounds=(), skills=(), languages=((10018, "English", "required"),),
             nationalities=(), study_levels=(), openings: int = 3, available: int = 3,
             applicants: int = 0, accepted: int = 0, duration: int | None = 8,
             cost: float | None = None, currency: str | None = None,
             opened: date | None = None, close: date | None = None, is_open: bool = True) -> dict:
    """Одна строка parser.opportunities (колонки + raw)."""
    today = date.today()
    opened = opened or today - timedelta(days=10)
    close = close or today + timedelta(days=30)
    prog_name = dict(PROGRAMMES)[programme_id]
    title = title or f"QA opportunity {oid}"
    cols = {
        "skills": [_req(c, n, o, "Professional Skills") for c, n, o in skills],
        "backgrounds": [_req(c, n, o) for c, n, o in backgrounds],
        "languages": [_req(c, n, o) for c, n, o in languages],
        "nationalities": [_req(c, n, o) for c, n, o in nationalities],
        "study_levels": [_study(c, n) for c, n in study_levels],
        "skills_developments": [],
    }
    raw = {"id": str(oid), "title": title, "status": "open",
           "programme": {"id": str(programme_id), "short_name_display": prog_name},
           "home_mc": {"id": str(mc[0]), "name": mc[1], "country_code": mc[2]},
           "host_lc": {"id": str(lc_id), "name": f"LC {lc_id}"},
           **cols}
    now = datetime.utcnow()
    return {
        "opportunity_id": oid, "title": title, "status": "open", "current_status": "open",
        "programme_id": programme_id, "programme_name": prog_name,
        "home_mc_id": mc[0], "home_mc_name": mc[1], "home_lc_id": lc_id, "home_lc_name": f"LC {lc_id}",
        "host_lc_id": lc_id, "host_lc_name": f"LC {lc_id}", "location": f"City {lc_id}",
        "organisation_id": 1, "organisation_name": "QA Company",
        "openings": openings, "available_openings": available,
        "applicants_count": applicants, "accepted_count": accepted,
        "date_opened": opened, "applications_close_date": close,
        "duration": duration, "cost_total": cost, "cost_currency": currency,
        "remote_updated_at": now,
        **{k: json.dumps(v) for k, v in cols.items()}, "raw": json.dumps(raw),
        "is_open": is_open, "source_query": "qa", "first_seen_at": now, "last_seen_at": now, "updated_at": now,
    }


def random_row(oid: int, rnd: random.Random) -> dict:
    """Случайная, но правдоподобная вакансия для нагрузочного и объёмного тестов."""
    opt = lambda: rnd.choice(["required", "required", "preferred"])
    pick = lambda pool, k: [(c, n, opt()) for c, n in rnd.sample(pool, k)]
    openings = rnd.randint(1, 8)
    applicants = rnd.randint(0, 120)
    paid = rnd.random() < 0.4
    langs = [(10018, "English", "required")] + pick(LANGS[1:], rnd.randint(0, 1))
    return make_row(
        oid, programme_id=rnd.choice([7, 8, 8, 9]),
        title=f"{rnd.choice(ROLES)} at {rnd.choice(COMPANIES)} [{rnd.choice([6, 8, 12, 24])} weeks]",
        mc=rnd.choice(COUNTRIES), lc_id=rnd.choice([941, 2441, 2452, 2848, 527, 100, 200, 300]),
        backgrounds=pick(BACKGROUNDS, rnd.randint(0, 2)), skills=pick(SKILLS, rnd.randint(0, 3)),
        languages=langs, nationalities=pick(NATIONS, 2) if rnd.random() < 0.1 else (),
        study_levels=rnd.sample(STUDY, 1) if rnd.random() < 0.2 else (),
        openings=openings, available=rnd.randint(1, openings), applicants=applicants,
        accepted=rnd.randint(0, min(applicants, openings)), duration=rnd.choice([6, 8, 12, 24, None]),
        cost=rnd.choice([150.0, 300.0, 600.0]) if paid else rnd.choice([0.0, None]),
        currency="EUR" if paid else None,
        opened=date.today() - timedelta(days=rnd.randint(0, 200)),
        close=date.today() + timedelta(days=rnd.randint(1, 120)),
    )


COLUMNS = ["opportunity_id", "title", "status", "current_status", "programme_id", "programme_name",
           "home_mc_id", "home_mc_name", "home_lc_id", "home_lc_name", "host_lc_id", "host_lc_name",
           "location", "organisation_id", "organisation_name", "openings", "available_openings",
           "applicants_count", "accepted_count", "date_opened", "applications_close_date", "duration",
           "cost_total", "cost_currency", "remote_updated_at", "skills", "backgrounds", "languages",
           "study_levels", "nationalities", "skills_developments", "raw", "is_open", "source_query",
           "first_seen_at", "last_seen_at", "updated_at"]
JSON_COLS = {"skills", "backgrounds", "languages", "study_levels", "nationalities", "skills_developments", "raw"}
INSERT_SQL = (
    "INSERT INTO parser.opportunities (" + ", ".join(COLUMNS) + ") VALUES ("
    + ", ".join(f"%({c})s::jsonb" if c in JSON_COLS else f"%({c})s" for c in COLUMNS) + ")"
)


def insert_rows(conn, rows: list[dict]) -> None:
    with conn.cursor() as cur:
        cur.executemany(INSERT_SQL, rows)
    conn.commit()


def delete_range(conn, lo: int, hi: int) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM parser.opportunities WHERE opportunity_id BETWEEN %s AND %s", (lo, hi))
        n = cur.rowcount
    conn.commit()
    return n
