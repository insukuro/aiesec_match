from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- доступ к AIESEC ---
    # Достаточно ЛЮБОГО из двух вариантов:
    #   а) AIESEC_TOKEN — готовый access_token;
    #   б) AIESEC_REFRESH_TOKEN + AIESEC_CLIENT_ID + AIESEC_CLIENT_SECRET — автообновление.
    # allow_no_token=true разрешает старт вообще без токена (ждём PUT /admin/token).
    aiesec_token: str | None = None
    aiesec_refresh_token: str | None = None
    aiesec_client_id: str | None = None
    aiesec_client_secret: str | None = None
    aiesec_auth_url: str = "https://auth.aiesec.org/oauth/token"
    aiesec_auth_origin: str | None = "https://aiesec.org"
    token_refresh_margin_sec: int = 600
    graphql_url: str = "https://gis-api.aiesec.org/graphql"

    allow_no_token: bool = False

    # --- БД ---
    database_url: str = "sqlite:///./data/parser.db"
    # Схема для таблиц приложения. В тестах (sqlite) выставляется "" — см. conftest.
    db_schema: str = "raw"

    targets_file: str = "targets.json"

    # --- нагрузка на AIESEC API ---
    per_page: int = 200
    max_pages: int = 200
    request_delay_sec: float = 0.7

    # --- планировщик ---
    scheduler_enabled: bool = True
    incremental_interval_minutes: int = 360
    reconcile_interval_hours: int = 24

    # --- инкремент ---
    incremental_date_filter: str = "created"
    incremental_overlap_days: int = 1

    # --- предохранители ---
    gap_fill_max: int = 200
    max_close_ratio: float = 0.5

    @field_validator(
        "aiesec_token", "aiesec_refresh_token", "aiesec_client_id", "aiesec_client_secret",
        "aiesec_auth_origin", mode="before",
    )
    @classmethod
    def _empty_to_none(cls, v):
        return (v.strip() or None) if isinstance(v, str) else v

    @model_validator(mode="after")
    def _check_credentials(self):
        has_any = bool(self.aiesec_token or self.aiesec_refresh_token)
        if not has_any and not self.allow_no_token:
            raise ValueError(
                "Задайте AIESEC_TOKEN или AIESEC_REFRESH_TOKEN (+ AIESEC_CLIENT_ID/SECRET), "
                "или включите ALLOW_NO_TOKEN=true, чтобы поднять сервис без токена"
            )
        if self.aiesec_refresh_token and not (self.aiesec_client_id and self.aiesec_client_secret):
            raise ValueError("Для AIESEC_REFRESH_TOKEN нужны AIESEC_CLIENT_ID и AIESEC_CLIENT_SECRET")
        return self

    @property
    def auto_refresh(self) -> bool:
        return bool(self.aiesec_client_id and self.aiesec_client_secret)


@dataclass
class Targets:
    countries: dict[str, int] = field(default_factory=dict)
    turkey_mc_id: int | None = None
    turkey_cities: dict[str, int] = field(default_factory=dict)
    base_filters: dict = field(default_factory=dict)
    only_with_openings: bool = True
    exclude_fields: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: str) -> "Targets":
        with open(path, encoding="utf-8") as fh:
            j = json.load(fh)
        tr = j.get("turkey") or {}
        return cls(
            countries=j.get("countries", {}),
            turkey_mc_id=tr.get("mc_id"),
            turkey_cities=tr.get("cities", {}),
            base_filters=j.get("base_filters", {"programmes": [8, 9], "status": "open"}),
            only_with_openings=j.get("only_with_openings", True),
            exclude_fields=j.get("exclude_fields", []),
        )

    @property
    def mc_ids(self) -> set[int]:
        return set(self.countries.values())

    @property
    def lc_ids(self) -> set[int]:
        return set(self.turkey_cities.values())

    def geo_queries(self) -> list[tuple[str, dict]]:
        out = []
        if self.countries:
            out.append(("countries", {"home_mcs": list(self.countries.values())}))
        if self.turkey_cities:
            out.append(("turkey_lcs", {"committee_scope": list(self.turkey_cities.values())}))
        return out