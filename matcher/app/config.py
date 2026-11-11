from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MATCHER_", extra="ignore")

    min_english: dict = {"talent": "B1", "teacher": "B2", "volunteer": "A2"}  # уточнить у экспертов
    catalog_source: str = "fake"          # fake | db
    fake_catalog_path: str = "app/data/fake_catalog.json"
    database_url: str = ""                # заполнится в Docker
    label_excellent: float = 0.75
    label_good: float = 0.55

@lru_cache
def get_settings() -> Settings:
    return Settings()