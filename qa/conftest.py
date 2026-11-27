"""Системные тесты всего сервиса: работают с уже поднятым стеком (make dev-up) как чёрный ящик.

Адреса берутся из переменных окружения. Значения по умолчанию подходят для запуска
внутри сети docker compose (см. docker-compose.qa.yml).
"""
import os
import uuid
from datetime import date, timedelta

import httpx
import psycopg
import pytest

from catalog_data import delete_range, insert_rows, make_row

BACKEND = os.environ.get("QA_BACKEND_URL", "http://backend:8000")
MATCHER = os.environ.get("QA_MATCHER_URL", "http://matcher:8000")
PARSER = os.environ.get("QA_PARSER_URL", "http://parser:8000")
QA_INTERNAL_TOKEN = os.environ.get("QA_INTERNAL_TOKEN", "")
DB = os.environ.get("QA_DB_NAME", "aiesec_match_dev")
DB_HOST = os.environ.get("QA_DB_HOST", "postgres")
DSN = {role: f"postgresql://{role}:{pw}@{DB_HOST}:5432/{DB}" for role, pw in {
    "parser_writer": os.environ.get("PARSER_DB_PASSWORD", "parser"),
    "backend_writer": os.environ.get("BACKEND_DB_PASSWORD", "backend"),
    "matcher_writer": os.environ.get("MATCHER_DB_PASSWORD", "matcher"),
}.items()}

API = f"{BACKEND}/api/v1"
QA_LO, QA_HI = 9_900_000, 9_900_999          # диапазон номеров тестовых вакансий
TODAY = date.today()


def connect(role: str) -> psycopg.Connection:
    return psycopg.connect(DSN[role], autocommit=False)


@pytest.fixture(scope="session")
def http():
    # отдельное соединение на запрос: после ответа 500 сервер рвёт соединение
    with httpx.Client(timeout=30, headers={"Connection": "close"}) as c:
        yield c


@pytest.fixture(scope="session")
def catalog():
    """Небольшой известный набор вакансий. Удаляется после прогона."""
    with connect("parser_writer") as conn:
        n = conn.execute("SELECT count(*) FROM parser.opportunities WHERE opportunity_id BETWEEN 8000000 AND 8999999"
                         ).fetchone()[0]
    if n:      # тысячи нагрузочных вакансий вытесняют тестовые из первой десятки подбора
        pytest.exit(f"В каталоге {n} нагрузочных вакансий. Сначала уберите их: python seed_catalog.py --clean", 2)
    EN = (10018, "English", "required")
    rows = [
        # 9900001: идеально подходит маркетологу из России (вакансия-образец 1340614 из реальной выдачи)
        make_row(QA_LO + 1, programme_id=8, title="QA Sales at Cooler Systems [8 weeks]",
                 backgrounds=[(10253, "Marketing", "required"), (10233, "Business administration", "required")],
                 skills=[(10161, "Sales", "required")],
                 languages=[EN, (10043, "Russian", "required")],
                 nationalities=[(10353, "Azerbaijan", "required"), (10463, "Russia", "required")],
                 study_levels=[(10785, "Bachelor")], duration=8, opened=TODAY - timedelta(days=5)),
        # 9900002: та же программа, но требования не совпадают с анкетой
        make_row(QA_LO + 2, programme_id=8, title="QA Data Analyst [12 weeks]",
                 backgrounds=[(10241, "Education", "required")], skills=[(11180, "Data Analysis", "required")],
                 languages=[EN], duration=12, applicants=90, opened=TODAY - timedelta(days=150)),
        # 9900003: волонтёрская, платная, Тунис
        make_row(QA_LO + 3, programme_id=7, title="QA Eco Volunteer [6 weeks]", mc=(1559, "Tunisia", "TN"),
                 languages=[EN], duration=6, cost=300.0, currency="EUR"),
        # 9900004: преподавание
        make_row(QA_LO + 4, programme_id=9, title="QA English Teacher [24 weeks]", languages=[EN], duration=24),
        # 9900005..7: не должны попадать в подбор
        make_row(QA_LO + 5, programme_id=8, title="QA closed", is_open=False),
        make_row(QA_LO + 6, programme_id=8, title="QA no places", available=0),
        make_row(QA_LO + 7, programme_id=8, title="QA deadline passed", close=TODAY - timedelta(days=1)),
    ]
    with connect("parser_writer") as conn:
        delete_range(conn, QA_LO, QA_HI)
        insert_rows(conn, rows)
    yield {"ideal": QA_LO + 1, "weak": QA_LO + 2, "volunteer": QA_LO + 3, "teacher": QA_LO + 4,
           "closed": QA_LO + 5, "full": QA_LO + 6, "expired": QA_LO + 7}
    with connect("parser_writer") as conn:
        delete_range(conn, QA_LO, QA_HI)


PROFILE = {
    "programmes": ["talent"], "birth_date": "2003-05-10", "english_level": "B2",
    "study": {"status": "bachelor", "course": 3, "specialty_text": "Маркетинг"},
    "other_languages": ["ru"], "work_experience": "none", "spheres": ["marketing", "sales"],
    "desired_countries": ["TR"], "duration": {"min_weeks": 6, "max_weeks": 12}, "start_window": "asap",
    "financial": {"willing_to_pay": True, "max_budget_eur": 500, "needs_stipend": False},
    "motivation_text": "Синтетическая анкета для тестов",
}


def new_email() -> str:
    return f"qa_{uuid.uuid4().hex[:12]}@example.com"


def consent_version(http: httpx.Client, kind: str = "pd_processing") -> str:
    response = http.get(f"{API}/meta/consents")
    assert response.status_code == 200, response.text
    return next(
        consent["version"]
        for consent in response.json()["consents"]
        if consent["kind"] == kind
    )


class User:
    """Зарегистрированный тестовый пользователь."""

    def __init__(self, http: httpx.Client, with_consent: bool = True, profile: dict | None = None):
        self.http, self.email, self.password = http, new_email(), "Passw0rd123"
        r = http.post(f"{API}/auth/register", json={"email": self.email, "password": self.password})
        assert r.status_code == 200, r.text
        self.h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        if with_consent:
            assert self.post(
                "/me/consents",
                json={
                    "kind": "pd_processing",
                    "version": consent_version(http),
                },
            ).status_code == 204
        if profile is not None:
            assert self.put("/profiles/me", json=profile).status_code == 200

    def _call(self, method, path, **kw):
        headers = {**self.h, **kw.pop("headers", {})}
        return self.http.request(method, f"{API}{path}", headers=headers, **kw)

    def get(self, path, **kw): return self._call("GET", path, **kw)
    def post(self, path, **kw): return self._call("POST", path, **kw)
    def put(self, path, **kw): return self._call("PUT", path, **kw)
    def delete(self, path, **kw): return self._call("DELETE", path, **kw)

    def recommend(self, body: dict | None = None, key: str | None = None):
        return self.post("/recommendations", json=body or {},
                         headers={"Idempotency-Key": key or str(uuid.uuid4())})


@pytest.fixture
def user(http):
    u = User(http, profile=PROFILE)
    yield u
    u.delete("/me")


@pytest.fixture
def bare_user(http):
    """Зарегистрирован, но без согласия и без анкеты."""
    u = User(http, with_consent=False)
    yield u
    u.delete("/me")
