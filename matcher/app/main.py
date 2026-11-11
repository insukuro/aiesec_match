from __future__ import annotations

from fastapi import FastAPI

from .routers import dictionaries, health, match

app = FastAPI(title="AIESEC matcher", version="0.1.0")
app.include_router(health.router)
app.include_router(match.router)
app.include_router(dictionaries.router)
