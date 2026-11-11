from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Set

import yaml

from app.schemas import ProfileSnapshot

CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"]
ENGLISH_ID = 10018


@lru_cache
def load_taxonomy() -> dict:
    with open(Path(__file__).parent / "taxonomy.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Profile:
    programmes: List[str]
    background_ids: Set[int]
    skill_ids: Set[int]
    language_ids: Set[int]            # все языки, кроме английского
    english_level: Optional[str]
    study_level_ids: Set[int]
    nationality_id: Optional[int]
    min_weeks: Optional[int]
    max_weeks: Optional[int]
    max_budget_eur: Optional[float]
    willing_to_pay: Optional[bool]
    preferred_lc_ids: Set[int]

    def languages_for(self, min_english: str) -> Set[int]:
        """Английский засчитываем, только если уровень не ниже порога программы."""
        ids = set(self.language_ids)
        if self.english_level and CEFR.index(self.english_level) >= CEFR.index(min_english):
            ids.add(ENGLISH_ID)
        return ids


def _sphere(name: str, tax: dict) -> dict:
    spheres = tax["spheres"]
    if name in spheres:
        return spheres[name]
    for key, val in spheres.items():          # teaching_* ловит teaching_kids и т.п.
        if key.endswith("*") and name.startswith(key[:-1]):
            return val
    return {}


def build_profile(s: ProfileSnapshot) -> Profile:
    tax = load_taxonomy()
    study = s.study or {}
    names = list(s.spheres) + list(s.activities) + ([study["field"]] if study.get("field") else [])

    bg, sk = set(), set()
    for name in names:
        m = _sphere(name, tax)
        bg.update(m.get("backgrounds", []))
        sk.update(m.get("skills", []))

    level = study.get("level")
    dur = s.duration or {}
    fin = s.financial or {}
    return Profile(
        programmes=list(s.programmes),
        background_ids=bg,
        skill_ids=sk,
        language_ids={tax["languages"][c] for c in s.other_languages if c in tax["languages"]},
        english_level=s.english_level,
        study_level_ids={tax["study_levels"][level]} if level in tax["study_levels"] else set(),
        nationality_id=tax["nationalities"].get(s.nationality) if s.nationality else None,
        min_weeks=dur.get("min_weeks"),
        max_weeks=dur.get("max_weeks"),
        max_budget_eur=fin.get("max_budget_eur"),
        willing_to_pay=fin.get("willing_to_pay"),
        preferred_lc_ids=set(s.preferred_lc_ids),
    )