from __future__ import annotations

from typing import Literal

from app.deps import load_dictionaries
from app.schemas import Dictionary
from fastapi import APIRouter

router = APIRouter()

@router.get("/dictionaries", response_model=Dictionary, tags=["service"])
def dictionary() -> Dictionary:
    return Dictionary

@router.get("/dictionaries/{name}", response_model=list[Dictionary], tags=["service"])
def get_dictionary_name(name:Literal["skills","languages","backgrounds"]):
    return load_dictionaries()[name]
