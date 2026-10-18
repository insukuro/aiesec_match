"""Жизненный цикл токенов AIESEC: загрузка при старте, сохранение, keepalive, диагностика."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime

from .auth import OAuthRefresher
from .client import AiesecClient, AiesecError, AuthError
from .config import Settings
from .models import utcnow
from .sync import SyncService

log = logging.getLogger("aiesec.tokens")


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def mask_token(t: str) -> str:
    return f"…{t[-4:]} (длина {len(t)})" if len(t) > 8 else "…"


def make_persist_tokens(service: SyncService):
    def persist_tokens(c: AiesecClient) -> None:
        """Сохраняет пару токенов одной транзакцией: refresh_token одноразовый."""
        service.set_states({
            "aiesec_token": c.token or "",
            "aiesec_refresh_token": c.refresh_token or "",
            "aiesec_token_expires_at": c.expires_at.isoformat() if c.expires_at else "",
            "aiesec_token_updated_at": utcnow().isoformat(),
        })
    return persist_tokens


def make_init_token(settings: Settings, client: AiesecClient, service: SyncService):
    def init_token() -> None:
        if not (settings.aiesec_token or settings.aiesec_refresh_token):
            log.warning(
                "AIESEC-токен не задан. Сервис поднялся в режиме ожидания. "
                "Загрузите токен: PUT /admin/token (token или refresh_token)"
            )
            return
        env_sha = _sha(f"{settings.aiesec_token or ''}|{settings.aiesec_refresh_token or ''}")
        if service.get_state("token_env_sha") != env_sha:
            service.set_states({
                "token_env_sha": env_sha,
                "aiesec_token": "",
                "aiesec_refresh_token": "",
                "aiesec_token_expires_at": "",
            })
        else:
            access = service.get_state("aiesec_token") or ""
            refresh = service.get_state("aiesec_refresh_token") or ""
            exp = service.get_state("aiesec_token_expires_at") or ""
            if access or refresh:
                client.set_token(
                    access or client.token, source="api",
                    refresh_token=refresh or None,
                    expires_at=datetime.fromisoformat(exp) if exp else None,
                )
                log.info("используются токены, сохранённые в БД (%s)", mask_token(client.token))
        try:
            client.ensure_fresh(refresh_if_unknown=True)
        except AiesecError as e:
            log.error("при старте не удалось обновить токен: %s", e)
    return init_token


def make_token_keepalive(client: AiesecClient):
    def token_keepalive() -> None:
        if client.auth_ok is False:
            return
        try:
            client.ensure_fresh()
        except AiesecError as e:
            log.error("keepalive: %s", e)
    return token_keepalive


def token_status(client: AiesecClient, service: SyncService) -> dict:
    left = client.seconds_left()
    return {
        "masked": mask_token(client.token) if client.token else None,
        "source": client.token_source,
        "auth": {True: "ok", False: "failed", None: "unknown"}[client.auth_ok],
        "auto_refresh": client.can_refresh,
        "expires_in_sec": int(left) if left is not None else None,
        "last_auth_error": client.auth_error,
        "checked_at": client.auth_checked_at,
        "updated_at": service.get_state("aiesec_token_updated_at"),
    }


def clean_token(v: str) -> str:
    return v.strip().strip("\"'").removeprefix("Bearer ").strip()