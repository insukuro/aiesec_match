from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import anyio.to_thread
from fastapi import FastAPI

from .config import get_settings
from .routers import dictionaries, health, match

log = logging.getLogger("matcher")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()

    # anyio-лимитер управляет числом ОДНОВРЕМЕННЫХ sync-эндпоинтов
    # (в том числе /v1/match). Это ровно тот параметр, который влияет
    # на sync-обработчики FastAPI. asyncio.set_default_executor на них
    # не действует — не путать.
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = s.thread_limiter_tokens

    # Отдельный executor для asyncio.to_thread (если где-то используется).
    # Размер = ядра * 2, чтобы CPU-bound задачи не дрались за GIL.
    workers = max(2, min(32, (os.cpu_count() or 4) * 2))
    executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cpu")
    import asyncio
    asyncio.get_running_loop().set_default_executor(executor)

    log.info(
        "matcher started: thread_limiter=%s cpu_workers=%s catalog_source=%s",
        s.thread_limiter_tokens, workers, s.catalog_source,
    )
    try:
        yield
    finally:
        executor.shutdown(wait=True)
        log.info("matcher stopped")


app = FastAPI(lifespan=lifespan, title="AIESEC matcher", version="0.1.0")
app.include_router(health.router)
app.include_router(match.router)
app.include_router(dictionaries.router)