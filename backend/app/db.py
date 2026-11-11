from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings

_engine = create_async_engine(
    get_settings().database_url,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
)

_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as s:
        yield s


async def read_only_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as s:
        await s.execute(text("SET TRANSACTION READ ONLY"))
        yield s