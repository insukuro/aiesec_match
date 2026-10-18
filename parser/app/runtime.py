"""Сборка зависимостей приложения. Импортируется один раз из main.py."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from .auth import OAuthRefresher
from .client import AiesecClient
from .config import Settings, Targets
from .models import make_session_factory
from .sync import SyncService
from .tokens import (
    make_init_token, make_persist_tokens, make_token_keepalive, token_status,
)

log = logging.getLogger("aiesec.runtime")

settings = Settings()
targets = Targets.load(settings.targets_file)
SessionLocal: sessionmaker = make_session_factory(settings.database_url)

refresher = (
    OAuthRefresher(
        settings.aiesec_auth_url, settings.aiesec_client_id, settings.aiesec_client_secret,
        origin=settings.aiesec_auth_origin,
    )
    if settings.auto_refresh
    else None
)

client = AiesecClient(
    token=settings.aiesec_token or "",
    url=settings.graphql_url,
    per_page=settings.per_page,
    max_pages=settings.max_pages,
    delay=settings.request_delay_sec,
    exclude_fields=targets.exclude_fields,
    refresher=refresher,
    refresh_token=settings.aiesec_refresh_token,
    refresh_margin=settings.token_refresh_margin_sec,
)
service = SyncService(client, settings, targets, SessionLocal)
scheduler = BackgroundScheduler(timezone="UTC")

persist_tokens = make_persist_tokens(service)
client.on_tokens = persist_tokens

init_token = make_init_token(settings, client, service)
token_keepalive = make_token_keepalive(client)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_token()
    if settings.scheduler_enabled:
        kw = dict(max_instances=1, coalesce=True)
        scheduler.add_job(service.run_now, "interval", args=["incremental"],
                          minutes=settings.incremental_interval_minutes, id="incremental", **kw)
        scheduler.add_job(service.run_now, "interval", args=["reconcile"],
                          hours=settings.reconcile_interval_hours, id="reconcile", **kw)
        scheduler.add_job(service.expire_by_deadline, "interval", hours=1, id="expire", **kw)
        if client.can_refresh:
            scheduler.add_job(token_keepalive, "interval", minutes=15, id="token_keepalive", **kw)
        if not service.has_bootstrapped():
            scheduler.add_job(service.run_now, args=["full"], id="bootstrap")
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    from .api import health, opportunities, sync as sync_api, admin

    app = FastAPI(title="AIESEC opportunities parser", version="1.1.0", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(opportunities.router)
    app.include_router(sync_api.router)
    app.include_router(admin.router)
    return app