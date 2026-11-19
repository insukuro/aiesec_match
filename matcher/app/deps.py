from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.config import get_settings
from app.repo.catalog_reader import CachedCatalogReader, DbCatalogReader, FakeCatalogReader
import logging
log = logging.getLogger("matcher.deps")


DATA_DIR = Path(__file__).parent / "data"
FILE_PREFIX = "_lists_"


@lru_cache(maxsize=1)
def load_dictionaries() -> dict[str, list[dict[str, Any]]]:
    """Читает справочники из app/data один раз; дальше отдаёт их из памяти."""
    return {
        path.stem.removeprefix(FILE_PREFIX): json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(DATA_DIR.glob(f"{FILE_PREFIX}*.json"))
    }


@lru_cache(maxsize=4)
def _build_reader(source: str, database_url: str, fake_path: str,
                  pool_size: int, max_overflow: int, cache_ttl: float):
    if source == "db":
        reader = DbCatalogReader(
            database_url, pool_size=pool_size, max_overflow=max_overflow,
        )
        if cache_ttl > 0:
            return CachedCatalogReader(reader, cache_ttl)
        return reader
    return FakeCatalogReader(fake_path)


def get_catalog_reader():
    s = get_settings()
    if s.catalog_source == "db" and not s.database_url:
        log.exception("failed to build catalog reader")
        raise HTTPException(503, detail={"type": "catalog-unavailable"})
    return _build_reader(
        s.catalog_source,
        s.database_url,
        s.fake_catalog_path,
        s.db_pool_size,
        s.db_max_overflow,
        s.catalog_cache_ttl_s,
    )