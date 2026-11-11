import os
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("AIESEC_DATABASE_URL", "sqlite+aiosqlite:///./test.db")

from app.main import app          # noqa: E402
from app import db as db_mod       # noqa: E402
from app.models import Base        # noqa: E402


@pytest_asyncio.fixture
async def engine():
    e = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield e
    await e.dispose()


@pytest_asyncio.fixture
async def session(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s


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