from __future__ import annotations

import json
from dataclasses import dataclass, field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aiesec_token: str  # обязателен, дефолта нет намеренно
    graphql_url: str = "https://gis-api.aiesec.org/graphql"
    database_url: str = "sqlite:///./data/parser.db"
    targets_file: str = "targets.json"
    api_key: str | None = None  # если задан — требуется заголовок X-API-Key

    # нагрузка на AIESEC API
    per_page: int = 200
    max_pages: int = 200
    request_delay_sec: float = 0.7  # пауза между любыми запросами к AIESEC

    # планировщик
    scheduler_enabled: bool = True
    incremental_interval_minutes: int = 360
    reconcile_interval_hours: int = 24

    # инкрементальная синхронизация
    incremental_date_filter: str = "created"  # имя фильтра в GraphQL: {from, to}
    incremental_overlap_days: int = 1  # запас по датам, upsert идемпотентен

    # предохранители
    gap_fill_max: int = 200  # сколько новых id догружать по одному, дальше — полный проход
    max_close_ratio: float = 0.5  # не закрывать >50% открытых разом (признак кривой выдачи)


@dataclass
class Targets:
    countries: dict[str, int] = field(default_factory=dict)  # название -> home_mc id
    turkey_mc_id: int | None = None
    turkey_cities: dict[str, int] = field(default_factory=dict)  # город -> LC id
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
