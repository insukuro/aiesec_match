from __future__ import annotations

import hashlib
import hmac
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Literal

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .auth import OAuthRefresher
from .client import AiesecClient, AiesecError, AuthError, NotSupported
from .config import Settings, Targets
from .models import Opportunity, SyncRun, make_session_factory, utcnow
from .sync import SyncService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("aiesec.app")

settings = Settings()
targets = Targets.load(settings.targets_file)
SessionLocal = make_session_factory(settings.database_url)
refresher = (OAuthRefresher(settings.aiesec_auth_url, settings.aiesec_client_id,
                            settings.aiesec_client_secret, origin=settings.aiesec_auth_origin)
             if settings.auto_refresh else None)
client = AiesecClient(
    token=settings.aiesec_token or "", url=settings.graphql_url, per_page=settings.per_page,
    max_pages=settings.max_pages, delay=settings.request_delay_sec,
    exclude_fields=targets.exclude_fields,
    refresher=refresher, refresh_token=settings.aiesec_refresh_token,
    refresh_margin=settings.token_refresh_margin_sec,
)
service = SyncService(client, settings, targets, SessionLocal)
scheduler = BackgroundScheduler(timezone="UTC")


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def mask_token(t: str) -> str:
    return f"…{t[-4:]} (длина {len(t)})" if len(t) > 8 else "…"


def persist_tokens(c) -> None:
    """Сохраняет пару токенов одной транзакцией. Вызывается клиентом после каждого обновления:
    refresh_token одноразовый, и без записи в БД цепочка не переживёт рестарт."""
    service.set_states({
        "aiesec_token": c.token or "",
        "aiesec_refresh_token": c.refresh_token or "",
        "aiesec_token_expires_at": c.expires_at.isoformat() if c.expires_at else "",
        "aiesec_token_updated_at": utcnow().isoformat(),
    })


client.on_tokens = persist_tokens


def init_token() -> None:
    """Какие токены использовать на старте.
    .env изменился с прошлого запуска (или это первый запуск) -> источник истины .env, сохранённое сбрасывается.
    Иначе берём то, что лежит в БД: оно новее, ведь refresh_token из .env после первого обновления уже недействителен."""
    env_sha = _sha(f"{settings.aiesec_token or ''}|{settings.aiesec_refresh_token or ''}")
    if service.get_state("token_env_sha") != env_sha:
        service.set_states({"token_env_sha": env_sha, "aiesec_token": "", "aiesec_refresh_token": "",
                            "aiesec_token_expires_at": ""})
    else:
        access = service.get_state("aiesec_token") or ""
        refresh = service.get_state("aiesec_refresh_token") or ""
        exp = service.get_state("aiesec_token_expires_at") or ""
        if access or refresh:
            client.set_token(access or client.token, source="api", refresh_token=refresh or None,
                             expires_at=datetime.fromisoformat(exp) if exp else None)
            log.info("используются токены, сохранённые в БД (%s)", mask_token(client.token))
    try:  # срок жизни неизвестен или токена нет — обновляемся сразу, чтобы дальше знать точное время
        client.ensure_fresh(refresh_if_unknown=True)
    except AiesecError as e:
        log.error("при старте не удалось обновить токен: %s", e)


def token_keepalive() -> None:
    """Раз в 15 минут: освежаем токен заранее, даже если синк сейчас не идёт."""
    if client.auth_ok is False:
        return  # refresh_token мёртв — ждём PUT /admin/token, не долбим сервер авторизации
    try:
        client.ensure_fresh()
    except AiesecError as e:
        log.error("keepalive: %s", e)


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
            scheduler.add_job(service.run_now, args=["full"], id="bootstrap")  # первый запуск — сразу
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="AIESEC opportunities parser", version="1.0.0", lifespan=lifespan)


def require_key(x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key and not hmac.compare_digest(x_api_key or "", settings.api_key):
        raise HTTPException(401, "Неверный или отсутствующий X-API-Key")


def get_db():
    with SessionLocal() as s:
        yield s


Auth = [Depends(require_key)]
LIST_EXCLUDE = {"raw"}


def to_dict(row: Opportunity, full: bool = False) -> dict:
    return {c.name: getattr(row, c.name) for c in Opportunity.__table__.columns
            if full or c.name not in LIST_EXCLUDE}


def _actual_clause():
    return (Opportunity.is_open.is_(True)) & (
        Opportunity.applications_close_date.is_(None) | (Opportunity.applications_close_date >= date.today()))


# ---------------- служебные ----------------
AUTH_LABEL = {True: "ok", False: "failed", None: "unknown"}


@app.get("/health")
def health():
    # 200 даже при мёртвом токене: рестарт контейнера его не починит, а статус виден в aiesec_auth
    return {"status": "ok", "sync_running": service.is_running(), "scheduler": scheduler.running,
            "aiesec_auth": AUTH_LABEL[client.auth_ok]}


# ---------------- стажировки ----------------
@app.get("/opportunities", dependencies=Auth)
def list_opportunities(
    country: str | None = Query(None, description="Название страны из targets.json"),
    city: str | None = Query(None, description="Город Турции из targets.json"),
    home_mc_id: int | None = None,
    home_lc_id: int | None = None,
    programme_id: int | None = None,
    q: str | None = Query(None, description="Поиск по названию"),
    only_open: bool = True,
    closing_before: date | None = None,
    new_since: datetime | None = Query(None, description="Впервые увидели после (UTC)"),
    updated_since: datetime | None = Query(None, description="Изменились/закрылись после (UTC): лента изменений для других сервисов. Используйте с only_open=false"),
    sort: Literal["first_seen_at", "applications_close_date", "date_opened", "updated_at"] = "first_seen_at",
    desc: bool = True,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    conds = []
    if only_open:
        conds.append(_actual_clause())
    if country:
        mc = next((v for k, v in targets.countries.items() if k.lower() == country.lower()), None)
        if mc is None:
            raise HTTPException(404, f"Страна '{country}' не в targets.json")
        conds.append(Opportunity.home_mc_id == mc)
    if city:
        lc = next((v for k, v in targets.turkey_cities.items() if k.lower() == city.lower()), None)
        if lc is None:
            raise HTTPException(404, f"Город '{city}' не в targets.json")
        conds.append(or_(Opportunity.home_lc_id == lc, Opportunity.host_lc_id == lc))
    if home_mc_id is not None:
        conds.append(Opportunity.home_mc_id == home_mc_id)
    if home_lc_id is not None:
        conds.append(Opportunity.home_lc_id == home_lc_id)
    if programme_id is not None:
        conds.append(Opportunity.programme_id == programme_id)
    if q:
        conds.append(Opportunity.title.ilike(f"%{q}%"))
    if closing_before:
        conds.append(Opportunity.applications_close_date <= closing_before)
    if new_since:
        conds.append(Opportunity.first_seen_at >= new_since)
    if updated_since:
        conds.append(Opportunity.updated_at >= updated_since)

    col = getattr(Opportunity, sort)
    total = db.scalar(select(func.count()).select_from(Opportunity).where(*conds))
    rows = db.scalars(select(Opportunity).where(*conds)
                      .order_by(col.desc() if desc else col.asc()).limit(limit).offset(offset)).all()
    return {"total": total, "limit": limit, "offset": offset, "items": [to_dict(r) for r in rows]}


@app.get("/opportunities/stats", dependencies=Auth)
def opportunities_stats(db: Session = Depends(get_db)):
    clause = _actual_clause()
    by_mc = dict(db.execute(select(Opportunity.home_mc_id, func.count()).where(clause)
                            .group_by(Opportunity.home_mc_id)).all())
    by_lc = dict(db.execute(select(Opportunity.home_lc_id, func.count()).where(clause)
                            .group_by(Opportunity.home_lc_id)).all())
    return {
        "open_total": db.scalar(select(func.count()).select_from(Opportunity).where(clause)),
        "countries": {n: by_mc.get(i, 0) for n, i in targets.countries.items()},
        "turkey_cities": {n: by_lc.get(i, 0) for n, i in targets.turkey_cities.items()},
        "last_full_at": service.get_state("last_full_at"),
        "last_incremental_at": service.get_state("last_incremental_at"),
        "last_reconcile_at": service.get_state("last_reconcile_at"),
    }


@app.get("/opportunities/{opportunity_id}", dependencies=Auth)
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    row = db.get(Opportunity, opportunity_id)
    if not row:
        raise HTTPException(404, "Стажировка не найдена в базе")
    return to_dict(row, full=True)


@app.post("/opportunities/{opportunity_id}/refresh", dependencies=Auth)
def refresh_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    """Перепроверить одну стажировку по id прямо в AIESEC (1 запрос)."""
    try:
        result = service.refresh_one(opportunity_id)
    except NotSupported as e:
        raise HTTPException(501, str(e))
    except AuthError as e:
        raise HTTPException(502, f"AIESEC отклонил токен: {e}")
    except AiesecError as e:
        raise HTTPException(502, f"Ошибка AIESEC API: {e}")
    db.expire_all()
    row = db.get(Opportunity, opportunity_id)
    return {**result, "opportunity": to_dict(row) if row else None}


# ---------------- синхронизация ----------------
@app.post("/sync/{kind}", status_code=202, dependencies=Auth)
def trigger_sync(kind: Literal["full", "incremental", "reconcile"], bg: BackgroundTasks):
    run_id = service.try_start(kind)
    if run_id is None:
        raise HTTPException(409, "Синхронизация уже выполняется")
    bg.add_task(service.execute, run_id, kind)
    return {"run_id": run_id, "kind": kind, "status": "running"}


@app.post("/maintenance/expire", dependencies=Auth)
def trigger_expire():
    """Локально закрыть стажировки с прошедшим дедлайном (без запросов к AIESEC)."""
    return {"closed": service.expire_by_deadline()}


@app.get("/sync/runs", dependencies=Auth)
def list_runs(limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.scalars(select(SyncRun).order_by(SyncRun.run_id.desc()).limit(limit)).all()
    return [{c.name: getattr(r, c.name) for c in SyncRun.__table__.columns} for r in rows]


# ---------------- админка / диагностика ----------------
@app.get("/admin/targets", dependencies=Auth)
def show_targets():
    return {"countries": targets.countries, "turkey_mc_id": targets.turkey_mc_id,
            "turkey_cities": targets.turkey_cities, "base_filters": targets.base_filters}


@app.get("/admin/offices", dependencies=Auth)
def find_offices(q: str = Query(..., min_length=2)):
    """Ручной поиск офисов (MC/LC) для пополнения targets.json."""
    try:
        return client.search_offices(q)
    except AiesecError as e:
        raise HTTPException(502, str(e))


@app.get("/admin/schema/filters", dependencies=Auth)
def schema_filters():
    """Какие фильтры реально умеет GraphQL AIESEC (если что-то поменяется)."""
    try:
        s = client.schema()
        return {"query": s.field, "item_type": s.item_type,
                "filters": sorted(s.filters), "broken_fields": sorted(client.broken_fields),
                "incremental_filter_ok": client.supports_range_filter(settings.incremental_date_filter)}
    except AiesecError as e:
        raise HTTPException(502, str(e))


# ---------------- токен AIESEC ----------------
class TokenIn(BaseModel):
    token: str | None = Field(None, min_length=10, max_length=2000,
                              description="Готовый access_token (живёт ~2 ч; без refresh-настроек сам не обновится)")
    refresh_token: str | None = Field(None, min_length=10, max_length=2000,
                                      description="refresh_token: меняется на access_token, дальше сервис обновляет токен сам")
    verify: bool = Field(True, description="Для token: проверить запросом к AIESEC до применения")
    run_sync: bool = Field(True, description="Если синк падал из-за токена (или первого синка ещё не было) — запустить сразу")

    @model_validator(mode="after")
    def _exactly_one(self):
        if bool(self.token) == bool(self.refresh_token):
            raise ValueError("Передайте ровно одно из полей: token или refresh_token")
        return self


def _clean(v: str) -> str:
    return v.strip().strip("\"'").removeprefix("Bearer ").strip()


def _token_status() -> dict:
    left = client.seconds_left()
    return {
        "masked": mask_token(client.token),
        "source": client.token_source,  # env | api | refresh
        "auth": AUTH_LABEL[client.auth_ok],
        "auto_refresh": client.can_refresh,
        "expires_in_sec": int(left) if left is not None else None,
        "last_auth_error": client.auth_error,
        "checked_at": client.auth_checked_at,
        "updated_at": service.get_state("aiesec_token_updated_at"),
    }


@app.get("/admin/token", dependencies=Auth)
def token_status():
    """Состояние токена AIESEC. Сами значения никогда не возвращаются."""
    return _token_status()


@app.post("/admin/token/check", dependencies=Auth)
def token_check():
    """Проверить текущий токен одним запросом."""
    try:
        ok, err = client.check_token()
    except AiesecError as e:
        raise HTTPException(502, str(e))
    return {"valid": ok, "error": err, **_token_status()}


@app.post("/admin/token/refresh", dependencies=Auth)
def token_refresh_now():
    """Принудительно обновить access_token через refresh_token (проверка, что автообновление работает)."""
    if not client.can_refresh:
        raise HTTPException(409, "Автообновление не настроено (нет refresh_token или client_id/secret)")
    try:
        client.refresh_after_401(client.token)  # тот же путь, что и при 401: безопасен при гонках
    except AuthError as e:
        raise HTTPException(422, str(e))
    except AiesecError as e:
        raise HTTPException(502, str(e))
    return _token_status()


@app.put("/admin/token", dependencies=Auth)
def put_token(body: TokenIn, bg: BackgroundTasks):
    """Заменить доступ к AIESEC без перезапуска.
    refresh_token -> сразу обменивается на access_token; дальше сервис обновляет его сам (нужны CLIENT_ID/SECRET).
    token -> применяется после проверки; при отказе AIESEC остаётся прежний.
    Всё сохраняется в БД и переживает рестарт, пока вы не измените значения в .env."""
    was_failing = client.auth_ok is False
    verified = None

    if body.refresh_token:
        if not client.refresher:
            raise HTTPException(422, "Автообновление не настроено: задайте AIESEC_CLIENT_ID и AIESEC_CLIENT_SECRET")
        try:
            client.refresh_with(_clean(body.refresh_token))  # применяет и сохраняет (on_tokens)
        except AuthError as e:
            raise HTTPException(422, f"{e}")
        except AiesecError as e:
            raise HTTPException(502, f"Не удалось обменять refresh_token: {e}")
        verified = True
    else:
        new = _clean(body.token)
        if len(new) < 10:
            raise HTTPException(422, "Токен слишком короткий после очистки")
        if body.verify:
            try:
                ok, err = client.check_token(new)
            except AiesecError as e:
                raise HTTPException(502, f"Не удалось проверить токен: {e}. Старый токен не менялся. "
                                         f"Повторите позже или передайте verify=false.")
            if not ok:
                raise HTTPException(422, f"AIESEC отклонил новый токен, оставлен прежний. Ответ: {err}")
            verified = True
        client.set_token(new, source="api", verified=verified)
        persist_tokens(client)
    log.info("доступ к AIESEC заменён через API (%s), проверен=%s", mask_token(client.token), verified)

    triggered = None
    if body.run_sync and (was_failing or not service.has_bootstrapped()):
        kind = "incremental" if service.has_bootstrapped() else "full"
        run_id = service.try_start(kind)
        if run_id is not None:
            bg.add_task(service.execute, run_id, kind)
            triggered = {"run_id": run_id, "kind": kind}
    return {**_token_status(), "verified": verified, "sync": triggered}