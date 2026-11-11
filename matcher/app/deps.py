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

from functools import lru_cache
from app.config import get_settings
from app.repo.catalog_reader import DbCatalogReader, FakeCatalogReader

@lru_cache
def get_catalog_reader():
    s = get_settings()
    if s.catalog_source == "db":
        return DbCatalogReader(s.database_url)
    return FakeCatalogReader(s.fake_catalog_path)
