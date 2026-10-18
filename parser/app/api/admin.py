from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from ..client import AiesecError, AuthError
from ..runtime import client, service, settings, targets
from ..runtime import client, service, persist_tokens
from ..tokens import clean_token as _clean, token_status as _token_status_impl
from .schemas import TokenIn

router = APIRouter()


def _token_status() -> dict:
    return _token_status_impl(client, service)


@router.get("/admin/targets", tags=["admin"])
def show_targets():
    return {
        "countries": targets.countries,
        "turkey_mc_id": targets.turkey_mc_id,
        "turkey_cities": targets.turkey_cities,
        "base_filters": targets.base_filters,
    }


@router.get("/admin/offices", tags=["admin"])
def find_offices(q: str = Query(..., min_length=2)):
    try:
        return client.search_offices(q)
    except AiesecError as e:
        raise HTTPException(502, str(e))


@router.get("/admin/schema/filters", tags=["admin"])
def schema_filters():
    try:
        s = client.schema()
        return {
            "query": s.field,
            "item_type": s.item_type,
            "filters": sorted(s.filters),
            "broken_fields": sorted(client.broken_fields),
            "incremental_filter_ok": client.supports_range_filter(settings.incremental_date_filter),
        }
    except AiesecError as e:
        raise HTTPException(502, str(e))


@router.get("/admin/token", tags=["admin"])
def token_status():
    return _token_status()


@router.post("/admin/token/check", tags=["admin"])
def token_check():
    try:
        ok, err = client.check_token()
    except AiesecError as e:
        raise HTTPException(502, str(e))
    return {"valid": ok, "error": err, **_token_status()}


@router.post("/admin/token/refresh", tags=["admin"])
def token_refresh_now():
    if not client.can_refresh:
        raise HTTPException(409, "Автообновление не настроено (нет refresh_token или client_id/secret)")
    try:
        client.refresh_after_401(client.token)
    except AuthError as e:
        raise HTTPException(422, str(e))
    except AiesecError as e:
        raise HTTPException(502, str(e))
    return _token_status()


@router.put("/admin/token", tags=["admin"])
def put_token(body: TokenIn, bg: BackgroundTasks):
    was_failing = client.auth_ok is False
    verified = None

    if body.refresh_token:
        if not client.refresher:
            raise HTTPException(422, "Автообновление не настроено: задайте AIESEC_CLIENT_ID и AIESEC_CLIENT_SECRET")
        try:
            client.refresh_with(_clean(body.refresh_token))
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
                raise HTTPException(
                    502,
                    f"Не удалось проверить токен: {e}. Старый токен не менялся. "
                    f"Повторите позже или передайте verify=false.",
                )
            if not ok:
                raise HTTPException(422, f"AIESEC отклонил новый токен, оставлен прежний. Ответ: {err}")
            verified = True
        client.set_token(new, source="api", verified=verified)
        persist_tokens(client)

    triggered = None
    if body.run_sync and (was_failing or not service.has_bootstrapped()):
        kind = "incremental" if service.has_bootstrapped() else "full"
        run_id = service.try_start(kind)
        if run_id is not None:
            bg.add_task(service.execute, run_id, kind)
            triggered = {"run_id": run_id, "kind": kind}
    return {**_token_status(), "verified": verified, "sync": triggered}