from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..formschema import load_form_schema

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/form-schema")
async def form_schema(response: Response):
    schema = load_form_schema()
    response.headers["Cache-Control"] = "public, max-age=300"
    response.headers["ETag"] = f'"{schema.get("version", "1")}"'
    return schema


@router.get("/form-options")
async def form_options(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(text("""
        SELECT programme_kind AS code, count(*) FILTER (WHERE is_open AND available_openings > 0) AS count
        FROM catalog.opportunity_v1 GROUP BY programme_kind
    """))).mappings().all()
    return {"programmes": [dict(r) for r in rows]}