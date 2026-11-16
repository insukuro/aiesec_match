from __future__ import annotations

from typing import Literal

from app.deps import load_dictionaries
from app.schemas import Dictionary
from fastapi import APIRouter

router = APIRouter()

NAMES = ("backgrounds", "languages", "skills")


@router.get("/dictionaries", response_model=list[str], tags=["service"])
def dictionary_names() -> list[str]:
    """Какие справочники можно запросить (BUG-M-04: раньше ручка отвечала 500)."""
    return list(NAMES)

@router.get("/dictionaries/{name}", response_model=list[Dictionary], tags=["service"])
def get_dictionary_name(name:Literal["skills","languages","backgrounds"]):
    return load_dictionaries()[name]
