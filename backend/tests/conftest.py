import os
import uuid

# Жёстко переопределяем, чтобы случайно не сходить в dev/prod БД.
os.environ["AIESEC_DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@postgres-test:5432/aiesec_test"
)
os.environ.setdefault("AIESEC_JWT_SECRET", "test-secret")
os.environ.setdefault("AIESEC_PROFILE_HMAC_SECRET", "test-hmac")

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import db as db_mod
from app.auth import issue_token, register_with_password, resolve_or_create_anonymous
from app.completeness import completeness
from app.config import get_settings
from app.main import app
from app.models import Base, Consent, Profile, ProfileVersion
from app.matcher_client import get_matcher




@pytest_asyncio.fixture
async def catalog_opps(engine):
    """Пара opportunities в parser.opportunities (catalog.* — view поверх них).
    id в диапазоне 9_000_000+, чтобы не пересечься с реальным каталогом.
    Возвращает (open_id, closed_id)."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    open_id, closed_id = 9_000_001, 9_000_002
    async with factory() as s:
        for oid, is_open in [(open_id, True), (closed_id, False)]:
            await s.execute(text("""
                INSERT INTO parser.opportunities
                    (opportunity_id, title, programme_id, home_mc_name,
                     host_lc_id, host_lc_name, location,
                     organisation_id, organisation_name,
                     openings, available_openings, applicants_count, accepted_count,
                     date_opened, applications_close_date,
                     earliest_start_date, latest_end_date, duration,
                     experience_type, cost_total, cost_currency,
                     raw, is_open, close_reason,
                     first_seen_at, last_seen_at, updated_at)
                VALUES
                    (:oid, :title, 8, 'Turkey',
                     1, 'LC Istanbul', 'Istanbul',
                     10, 'Org',
                     5, 3, 1, 0,
                     now()::date, (now() + interval '30 days')::date,
                     (now() + interval '40 days')::date, (now() + interval '90 days')::date, 8,
                     'volunteer', 100, 'EUR',
                     '{"home_mc": {"iso_code": "TR"}}'::jsonb, :is_open, NULL,
                     now(), now(), now())
                ON CONFLICT (opportunity_id) DO NOTHING
            """), {"oid": oid, "title": f"Opp {oid} [8 weeks]", "is_open": is_open})
        await s.commit()
    return open_id, closed_id



class FakeMatcher:
    def __init__(self):
        self.response = {"groups": [], "programme_prior": []}
        self.calls: list[dict] = []
        self.raise_exc: Exception | None = None

    async def match(self, payload):
        self.calls.append(payload)
        if self.raise_exc:
            raise self.raise_exc
        return self.response

    async def aclose(self):
        pass


@pytest.fixture
def fake_matcher():
    fake = FakeMatcher()
    app.dependency_overrides[get_matcher] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_matcher, None)



@pytest_asyncio.fixture
async def engine():
    from app.config import get_settings
    eng = create_async_engine(get_settings().database_url)
    async with eng.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()
    
@pytest_asyncio.fixture
async def session(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
        await s.rollback()


@pytest_asyncio.fixture
async def client(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override():
        async with factory() as s:
            yield s

    app.dependency_overrides[db_mod.get_session] = override
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    app.dependency_overrides.clear()


# --- matcher ---

class FakeMatcher:
    def __init__(self):
        self.response = {"groups": [], "programme_prior": []}
        self.calls: list[dict] = []
        self.raise_exc: Exception | None = None

    async def match(self, payload):
        self.calls.append(payload)
        if self.raise_exc:
            raise self.raise_exc
        return self.response

    async def aclose(self):
        pass


@pytest.fixture
def fake_matcher():
    """Подменяет app.state.matcher на фейк. Lifespan его не перетрёт,
    т.к. фикстура применяется уже после входа в клиент."""
    fake = FakeMatcher()
    app.state.matcher = fake
    return fake


# --- пользователи ---

@pytest_asyncio.fixture
async def registered_user(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        email = f"u{uuid.uuid4().hex[:8]}@test.io"
        user = await register_with_password(s, email, "Passw0rd!")
        return user, email


@pytest.fixture
def auth_headers(registered_user):
    user, _ = registered_user
    tok, _ = issue_token(user.user_id, 3600)
    return {"Authorization": f"Bearer {tok}"}


@pytest_asyncio.fixture
async def anon_user(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        user, secret = await resolve_or_create_anonymous(s, None)
        return user, secret


@pytest.fixture
def guest_headers(anon_user):
    user, _ = anon_user
    tok, _ = issue_token(user.user_id, 3600)
    return {"Authorization": f"Bearer {tok}"}


# --- профиль ---

VALID_PROFILE = {
    "programmes": ["talent"],
    "birth_date": "2000-01-01",
    "study": {"status": "bachelor"},
    "english_level": "B2",
    "spheres": ["it"],
    "desired_countries": ["TR"],
    "duration": {"min_weeks": 6},
    "start_window": "asap",
    "motivation_text": "хочу поехать",
}


@pytest_asyncio.fixture
async def user_with_consent(engine, registered_user):
    """Зарегистрированный юзер + pd_processing consent, без профиля."""
    user, email = registered_user
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        s.add(Consent(user_id=user.user_id, kind="pd_processing", version="1"))
        await s.commit()
    return user, email


@pytest_asyncio.fixture
async def user_with_profile(engine, user_with_consent):
    """Юзер + consent + валидный профиль v1."""
    user, email = user_with_consent
    body = dict(VALID_PROFILE)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        s.add(Profile(user_id=user.user_id, current_version=1))
        s.add(ProfileVersion(
            user_id=user.user_id, version=1, body=body,
            birth_date=None, completeness=completeness(body),
        ))
        await s.commit()
    return user, email