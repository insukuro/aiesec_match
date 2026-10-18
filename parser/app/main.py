"""Точка входа. Реэкспортирует всё, что тесты/интеграции могут захотеть импортировать."""
from __future__ import annotations

import logging

# Настройка логирования — один раз, до первого использования логгеров.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from .runtime import (  # noqa: E402,F401
    SessionLocal,
    client,
    create_app,
    init_token,
    persist_tokens,
    scheduler,
    service,
    settings,
    targets,
    token_keepalive,
)
from .tokens import clean_token as _clean, mask_token  # noqa: E402,F401

app = create_app()

__all__ = [
    "app", "settings", "targets", "client", "service", "SessionLocal",
    "scheduler", "init_token", "persist_tokens", "token_keepalive",
    "_clean", "mask_token",
]