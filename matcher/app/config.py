from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MATCHER_", extra="ignore")

    min_english: dict[str, str] = Field(
        default_factory=lambda: {"talent": "B1", "teacher": "B2", "volunteer": "A2"},
    )
    catalog_source: Literal["db", "fake"] = "db"
    fake_catalog_path: str = "app/data/fake_catalog.json"
    database_url: str = ""
    catalog_cache_ttl_s: float = 0          # 0 = кэш выключен; в проде 60
    label_excellent: float = 0.75
    label_good: float = 0.55

    # Пул SQLAlchemy должен быть согласован с anyio-лимитером (см. main.py).
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Сколько sync-эндпоинтов FastAPI может выполнять одновременно.
    # Дефолт anyio — 40; для CPU-bound ranking этого часто мало.
    thread_limiter_tokens: int = 80



@lru_cache
def get_settings() -> Settings:
    return Settings()