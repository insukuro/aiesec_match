"""Преобразование анкеты в профиль для расчёта (app/domain/profile.py).

Файл появился после прогона контрольных дефектов: ошибка D27 (сфера анкеты
превращается не в то требование) осталась незамеченной, значит тестов на этот шаг не было.
"""
import pytest

from app.domain.profile import build_profile
from app.schemas import ProfileSnapshot


def profile(**kw):
    return build_profile(ProfileSnapshot(**kw))


@pytest.mark.parametrize("spheres, backgrounds, skills", [
    (["marketing"], {10253}, set()),
    (["sales"], {21677}, {10161}),
    (["marketing", "sales"], {10253, 21677}, {10161}),
    (["teaching_kids"], {10241}, {10162}),            # teaching_* ловит любое teaching_...
    (["космонавтика"], set(), set()),                  # неизвестная сфера не ошибка
])
def test_spheres_become_backgrounds_and_skills(spheres, backgrounds, skills):
    p = profile(spheres=spheres)
    assert p.background_ids == backgrounds and p.skill_ids == skills

def test_activities_and_study_field_count_too():
    p = profile(activities=["sales"], study={"field": "marketing"})
    assert p.background_ids == {10253, 21677} and p.skill_ids == {10161}

def test_languages_nationality_study_level():
    p = profile(other_languages=["ru", "es", "xx"], nationality="AZ", study={"status": "school"})
    assert p.language_ids == {10043, 10048}
    assert p.nationality_id == 10353
    assert p.study_level_ids == {10782}

def test_english_is_added_only_from_threshold():
    p = profile(english_level="B1", other_languages=["ru"])
    assert p.languages_for("B1") == {10043, 10018}
    assert p.languages_for("B2") == {10043}

def test_numbers_are_copied():
    p = profile(duration={"min_weeks": 6, "max_weeks": 12},
                financial={"willing_to_pay": False, "max_budget_eur": 250.5}, preferred_lc_ids=[941, 941])
    assert (p.min_weeks, p.max_weeks, p.max_budget_eur, p.willing_to_pay) == (6, 12, 250.5, False)
    assert p.preferred_lc_ids == {941}

def test_empty_profile_has_no_requirements():
    p = profile()
    assert not (p.background_ids or p.skill_ids or p.language_ids or p.study_level_ids)
    assert p.nationality_id is None and p.max_budget_eur is None
