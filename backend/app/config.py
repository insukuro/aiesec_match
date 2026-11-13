from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AIESEC_", extra="ignore")

    database_url: str = "postgresql+asyncpg://backend_writer:backend@postgres:5432/aiesec_match"
    jwt_secret: str = "change-me"
    jwt_ttl_seconds: int = 24 * 3600
    telegram_bot_token: str = ""
    profile_hmac_secret: str = "change-me-hmac"

    matcher_base_url: str = "http://matcher:8000"
    matcher_timeout_s: float = 3.0

    age_min: int = 16
    age_max: int = 35
    request_body_max_bytes: int = 64 * 1024
    rate_limit_per_minute: int = 60
    recommendations_per_minute: int = 10

    form_schema_path: Path = Path("app/forms/form_schema.v1.yaml")
    openapi_path: Path = Path("openapi/backend.v1.json")


@lru_cache
def get_settings() -> Settings:
    return Settings()