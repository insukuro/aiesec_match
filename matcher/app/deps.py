from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
FILE_PREFIX = "_lists_"


@lru_cache(maxsize=1)
def load_dictionaries() -> dict[str, list[dict[str, Any]]]:
    """Читает справочники из app/data один раз; дальше отдаёт их из памяти."""
    return {
        path.stem.removeprefix(FILE_PREFIX): json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(DATA_DIR.glob(f"{FILE_PREFIX}*.json"))
    }

from fastapi import HTTPException

from app.config import get_settings
from app.repo.catalog_reader import CachedCatalogReader, DbCatalogReader, FakeCatalogReader


@lru_cache(maxsize=1)
def _build_reader():
    s = get_settings()
    if s.catalog_source == "db":
        reader = DbCatalogReader(s.database_url)
        if s.catalog_cache_ttl_s > 0:
            return CachedCatalogReader(reader, s.catalog_cache_ttl_s)
        return reader
    return FakeCatalogReader(s.fake_catalog_path)


def get_catalog_reader():
    """Источник каталога. Ошибка настройки (нет адреса БД, нет файла) это 503, а не 500 (BUG-M-09)."""
    try:
        return _build_reader()
    except Exception as e:
        raise HTTPException(503, detail={"type": "catalog-unavailable"}) from e
