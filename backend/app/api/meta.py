from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.meta_service import MetaService
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
    return await MetaService(session).form_options()