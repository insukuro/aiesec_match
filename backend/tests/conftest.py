# backend/tests/conftest.py
"""Общие фикстуры backend-тестов.

Два драйвера живут одновременно и это осознанно:
  * asyncpg  — приложение (app/db.py: create_async_engine)
  * psycopg  — фикстуры, которые пишут в parser.opportunities напрямую

Импорт psycopg — ТОЛЬКО внутри фикстур: prod-образ (backend.txt без psycopg)
импортирует conftest и не должен падать.
"""

import inspect
import os
import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio

# --- 1. env ДО импорта app.* -------------------------------------------------
os.environ.setdefault(
    "AIESEC_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/aiesec_test",
)
os.environ.setdefault("AIESEC_MATCHER_BASE_URL", "http://localhost:8002")
os.environ.setdefault("AIESEC_JWT_SECRET", "test-jwt")
os.environ.setdefault("AIESEC_PROFILE_HMAC_SECRET", "test-hmac")

# --- 2. импорты приложения ---------------------------------------------------
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db import _engine, _session_factory, get_session  # noqa: E402
from app.main import app  # noqa: E402


def pytest_collection_modifyitems(items):
    for item in items:
        if inspect.iscoroutinefunction(getattr(item, "obj", None)):
            item.add_marker(pytest.mark.asyncio(loop_scope="session"), append=False)


# --- 3. DSN для psycopg-фикстур ----------------------------------------------
def _psycopg_dsn() -> str:
    return os.environ["AIESEC_DATABASE_URL"].replace(
        "postgresql+asyncpg://", "postgresql://", 1
    )


def _connect_psycopg():
    import psycopg
    return psycopg.connect(_psycopg_dsn(), autocommit=False)


# --- 4. ASGI-клиент ----------------------------------------------------------
@pytest_asyncio.fixture(scope="session")
async def client():
    from asgi_lifespan import LifespanManager

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            timeout=30,
            headers={"Connection": "close"},
        ) as c:
            yield c


# --- 5. Сессия ---------------------------------------------------------------
@pytest_asyncio.fixture
async def session() -> AsyncSession:
    async with _session_factory() as s:
        yield s


@pytest_asyncio.fixture(autouse=True)
async def _override_session():
    async def _get_session_override():
        async with _session_factory() as request_session:
            yield request_session

    app.dependency_overrides[get_session] = _get_session_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_session, None)

# --- 6. Валидный профиль -----------------------------------------------------
VALID_PROFILE = {
    "programmes": ["talent"],
    "birth_date": "2003-05-10",
    "english_level": "B2",
    "study": {"status": "bachelor", "course": 3, "specialty_text": "Маркетинг"},
    "other_languages": ["ru"],
    "work_experience": "none",
    "spheres": ["marketing", "sales"],
    "desired_countries": ["TR"],
    "duration": {"min_weeks": 6, "max_weeks": 12},
    "start_window": "asap",
    "financial": {"willing_to_pay": True, "max_budget_eur": 500, "needs_stipend": False},
    "motivation_text": "Синтетическая анкета для тестов",
}


# --- 7. Пользователь ---------------------------------------------------------
def _new_email() -> str:
    return f"test_{uuid.uuid4().hex[:12]}@example.com"


class TestUser:
    """Зарегистрированный пользователь для API-тестов профиля."""

    def __init__(self, client: AsyncClient, with_consent: bool = True):
        self.client = client
        self.email = _new_email()
        self.password = "Passw0rd123"
        self.user_id: uuid.UUID | None = None
        self.headers: dict[str, str] = {}
        self._with_consent = with_consent

    async def register(self) -> None:
        r = await self.client.post(
            "/api/v1/auth/register",
            json={"email": self.email, "password": self.password},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # user_id: в разных API встречается как user_id / id / sub — берём что есть
        self.user_id = body.get("user_id") or body.get("id")
        if self.user_id is None:
            # fallback: декодируем sub из JWT (payload middle part)
            import base64, json as _json
            payload = body["access_token"].split(".")[1]
            payload += "=" * (-len(payload) % 4)
            data = _json.loads(base64.urlsafe_b64decode(payload))
            self.user_id = uuid.UUID(data["sub"])
        self.headers = {"Authorization": f"Bearer {body['access_token']}"}

        if self._with_consent:
            r = await self.client.post(
                "/api/v1/me/consents",
                json={"kind": "pd_processing", "version": "2.0"},
                headers=self.headers,
            )
            assert r.status_code == 204, r.text

    async def put_profile(self, payload: dict | None = None) -> dict:
        r = await self.client.put(
            "/api/v1/profiles/me",
            json=payload or VALID_PROFILE,
            headers=self.headers,
        )
        assert r.status_code == 200, r.text
        return r.json()

    async def cleanup(self) -> None:
        try:
            await self.client.delete("/api/v1/me", headers=self.headers)
        except Exception:
            pass


@pytest_asyncio.fixture
async def user(client):
    """Зарегистрирован + согласие. Профиля нет."""
    u = TestUser(client, with_consent=True)
    await u.register()
    yield u
    await u.cleanup()


@pytest_asyncio.fixture
async def bare_user(client):
    """Зарегистрирован, без согласия и без анкеты."""
    u = TestUser(client, with_consent=False)
    await u.register()
    yield u
    await u.cleanup()


@pytest_asyncio.fixture
async def auth_headers(user):
    """Готовые заголовки для user."""
    return user.headers


@pytest_asyncio.fixture
async def fake_matcher(client):
    class FakeMatcher:
        def __init__(self):
            self.calls = []
            self.response = {"programme_prior": [], "groups": []}
            self.raise_exc = None

        async def match(self, payload):
            self.calls.append(payload)
            if self.raise_exc is not None:
                raise self.raise_exc
            return self.response

    original_matcher = app.state.matcher
    matcher = FakeMatcher()
    app.state.matcher = matcher
    try:
        yield matcher
    finally:
        app.state.matcher = original_matcher

@pytest_asyncio.fixture
async def user_with_consent(user):
    """Совместимость с test_api_profiles.py: возвращает (user, session)."""
    # session уже открыта через autouse _override_session -> session
    from app.db import _session_factory
    async with _session_factory() as s:
        yield user, s


@pytest_asyncio.fixture
async def user_with_profile(user):
    """Зарегистрирован + согласие + профиль v1. Возвращает (user, session)."""
    await user.put_profile()
    from app.db import _session_factory
    async with _session_factory() as s:
        yield user, s


# --- 8. Каталог вакансий (psycopg) ------------------------------------------
CATALOG_LO, CATALOG_HI = 9_800_000, 9_800_999


@pytest.fixture(scope="session")
def catalog_rows():
    from catalog_data import delete_range, insert_rows, make_row

    today = date.today()
    EN = (10018, "English", "required")
    rows = [
        make_row(CATALOG_LO + 1, programme_id=8, title="Test Sales [8 weeks]",
                 backgrounds=[(10253, "Marketing", "required")],
                 languages=[EN], duration=8, opened=today - timedelta(days=5)),
        make_row(CATALOG_LO + 2, programme_id=9, title="Test Teacher [24 weeks]",
                 languages=[EN], duration=24, is_open=False),
    ]
    with _connect_psycopg() as conn:
        delete_range(conn, CATALOG_LO, CATALOG_HI)
        insert_rows(conn, rows)
    yield {"ideal": CATALOG_LO + 1, "teacher": CATALOG_LO + 2}
    with _connect_psycopg() as conn:
        delete_range(conn, CATALOG_LO, CATALOG_HI)


@pytest.fixture
def catalog_opps(catalog_rows):
    return catalog_rows["ideal"], catalog_rows["teacher"]


# --- 9. Очистка движка -------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def _dispose_engine():
    yield
    await _engine.dispose()