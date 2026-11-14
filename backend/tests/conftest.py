import os

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault(
    "AIESEC_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres-test:5432/aiesec_test",
)

from app import db as db_mod  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest_asyncio.fixture
async def engine():
    """Function-scoped: engine живёт в том же loop, что и тест."""
    from app.config import get_settings
    eng = create_async_engine(get_settings().database_url)
    async with eng.begin() as conn:
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

    # подменяем engine в модуле db, чтобы app.state.matcher и lifespan
    # не тянули session-scoped engine
    app.dependency_overrides[db_mod.get_session] = override
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    app.dependency_overrides.clear()