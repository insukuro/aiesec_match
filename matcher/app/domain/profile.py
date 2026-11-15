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
    study, dur, fin = s.study, s.duration, s.financial
    names = list(s.spheres) + list(s.activities) + ([study.field] if study and study.field else [])

    bg, sk = set(), set()
    for name in names:
        m = _sphere(name, tax)
        bg.update(m.get("backgrounds", []))
        sk.update(m.get("skills", []))

    # анкета присылает study.status, старые клиенты могли присылать study.level (BUG-M-10)
    level = (study.level or study.status) if study else None
    # коды языков и стран сравниваем без учёта регистра (BUG-M-07)
    langs = {c.lower() for c in s.other_languages}
    nationality = s.nationality.upper() if s.nationality else None
    return Profile(
        programmes=list(s.programmes),
        background_ids=bg,
        skill_ids=sk,
        language_ids={tax["languages"][c] for c in langs if c in tax["languages"]},
        english_level=s.english_level,
        study_level_ids={tax["study_levels"][level]} if level in tax["study_levels"] else set(),
        nationality_id=tax["nationalities"].get(nationality) if nationality else None,
        min_weeks=dur.min_weeks if dur else None,
        max_weeks=dur.max_weeks if dur else None,
        max_budget_eur=fin.max_budget_eur if fin else None,
        willing_to_pay=fin.willing_to_pay if fin else None,
        preferred_lc_ids=set(s.preferred_lc_ids),
    )