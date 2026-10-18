from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import SyncRun
from ..runtime import service
from .deps import get_db

router = APIRouter()


@router.post("/sync/{kind}", status_code=202, tags=["sync"])
def trigger_sync(kind: Literal["full", "incremental", "reconcile"], bg: BackgroundTasks):
    run_id = service.try_start(kind)
    if run_id is None:
        raise HTTPException(409, "Синхронизация уже выполняется")
    bg.add_task(service.execute, run_id, kind)
    return {"run_id": run_id, "kind": kind, "status": "running"}


@router.post("/maintenance/expire", tags=["sync"])
def trigger_expire():
    return {"closed": service.expire_by_deadline()}


@router.get("/sync/runs", tags=["sync"])
def list_runs(limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.scalars(select(SyncRun).order_by(SyncRun.run_id.desc()).limit(limit)).all()
    return [{c.name: getattr(r, c.name) for c in SyncRun.__table__.columns} for r in rows]