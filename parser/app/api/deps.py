"""Зависимости FastAPI."""
from __future__ import annotations

from ..runtime import SessionLocal


def get_db():
    with SessionLocal() as s:
        yield s