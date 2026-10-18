from __future__ import annotations

from fastapi import APIRouter

from ..runtime import client, scheduler, service

router = APIRouter()

AUTH_LABEL = {True: "ok", False: "failed", None: "unknown"}


@router.get("/health", tags=["service"])
def health():
    return {
        "status": "ok",
        "sync_running": service.is_running(),
        "scheduler": scheduler.running,
        "aiesec_auth": AUTH_LABEL[client.auth_ok],
    }