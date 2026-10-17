"""Обмен refresh_token -> access_token (OAuth2, auth.aiesec.org).

Важно: AIESEC ротирует refresh_token — в каждом ответе приходит НОВЫЙ, а старый, судя по всему,
перестаёт работать. Поэтому новый refresh_token нужно сохранить до того, как мы начнём пользоваться
результатом. Это делает AiesecClient через колбэк on_tokens (запись в БД).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

from .errors import AiesecError, AuthError

log = logging.getLogger("aiesec.auth")


@dataclass
class TokenSet:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None  # naive UTC
    scope: str | None = None


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OAuthRefresher:
    def __init__(self, url: str, client_id: str, client_secret: str, origin: str | None = None,
                 timeout: int = 30, session: requests.Session | None = None):
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.origin = origin
        self.timeout = timeout
        self._http = session or requests.Session()

    def refresh(self, refresh_token: str) -> TokenSet:
        headers = {"Accept": "application/json"}
        if self.origin:
            headers["Origin"] = self.origin
        try:
            r = self._http.post(
                self.url,
                auth=(self.client_id, self.client_secret),  # HTTP Basic, как curl -u
                data={"grant_type": "refresh_token", "refresh_token": refresh_token},
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise AiesecError(f"сервер авторизации AIESEC недоступен: {e}") from e

        if r.status_code in (400, 401, 403):
            # invalid_grant: refresh_token протух, уже использован или отозван
            raise AuthError(f"refresh_token отклонён ({r.status_code}): {r.text[:300]}. "
                            f"Нужен новый refresh_token: PUT /admin/token")
        if r.status_code != 200:
            raise AiesecError(f"сервер авторизации ответил HTTP {r.status_code}: {r.text[:200]}")
        try:
            j = r.json()
            access = j["access_token"]
        except (ValueError, KeyError) as e:
            raise AiesecError(f"неожиданный ответ сервера авторизации: {r.text[:200]}") from e

        return TokenSet(access_token=access, refresh_token=j.get("refresh_token"),
                        expires_at=self._expires_at(j), scope=j.get("scope"))

    @staticmethod
    def _expires_at(j: dict) -> datetime | None:
        try:
            ttl = int(j["expires_in"])
        except (KeyError, TypeError, ValueError):
            return None
        now = utcnow()
        local = now + timedelta(seconds=ttl)
        try:  # created_at от сервера точнее, но защищаемся от рассинхрона часов
            by_server = datetime.fromtimestamp(int(j["created_at"]) + ttl, timezone.utc).replace(tzinfo=None)
        except (KeyError, TypeError, ValueError, OverflowError):
            return local
        return by_server if abs((by_server - local).total_seconds()) < 300 else local