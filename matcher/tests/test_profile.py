"""Преобразование анкеты в профиль для расчёта (app/domain/profile.py).

Файл появился после прогона контрольных дефектов: ошибка D27 (сфера анкеты
превращается не в то требование) осталась незамеченной, значит тестов на этот шаг не было.
"""
import pytest

from app.domain.profile import build_profile
from app.schemas import ProfileSnapshot


MARKETING_SK = {11186, 11176, 11205, 11193, 11203}
SALES_SK = {10161, 11195, 10163, 11200}


@pytest.mark.parametrize("spheres, backgrounds, skills", [
    (["marketing"], {10253, 10265, 10237}, MARKETING_SK),
    (["sales"], {21677}, SALES_SK),
    (["marketing", "sales"], {10253, 10265, 10237, 21677}, MARKETING_SK | SALES_SK),
    (["teaching_kids"], {10241, 10263}, {10162, 11173}),
    (["teaching"], {10241}, {10162, 10157}),
    (["it"], {10239, 10268, 10238, 11298, 10255, 11297}, {11260, 11180, 11221, 11225}),
    (["events"], {10237, 10265}, {11187, 10156, 11194}),
    (["космонавтика"], set(), set()),
])
def test_spheres_become_backgrounds_and_skills(spheres, backgrounds, skills):
    p = profile(spheres=spheres)
    assert p.background_ids == backgrounds and p.skill_ids == skills


def test_activities_and_study_field_count_too():
    p = profile(activities=["sales"], study={"field": "marketing"})
    assert p.background_ids == {10253, 10265, 10237, 21677}
    assert p.skill_ids == MARKETING_SK | SALES_SK
    
    
def profile(**kw):
    return build_profile(ProfileSnapshot(**kw))

def test_languages_nationality_study_level():
    p = profile(other_languages=["ru", "es", "xx"], nationality="AZ", study={"status": "school"})
    assert p.language_ids == {10043, 10048}
    assert p.nationality_id == 10353
    assert p.study_level_ids == {10782}

def test_english_in_other_languages_does_not_bypass_threshold():
    # en нет в taxonomy.languages: английский считается только по english_level
    p = profile(english_level="A1", other_languages=["en", "ru"])
    assert p.language_ids == {10043}
    assert p.languages_for("B1") == {10043}


def test_every_form_option_is_in_taxonomy():
    # все сферы и активности, которые предлагает анкета backend (meta_service.STATIC_OPTIONS)
    from app.domain.profile import load_taxonomy
    form = {"it", "marketing", "sales", "finance", "hr", "design", "engineering", "education",
            "healthcare", "ngo", "teaching", "events", "ecology", "community", "culture", "sports"}
    assert form <= set(load_taxonomy()["spheres"])


def test_taxonomy_ids_exist_in_dictionaries():
    # опечатка в коде не должна пройти незамеченной: каждый id есть в справочнике app/data
    from app.deps import load_dictionaries
    from app.domain.profile import load_taxonomy
    d = load_dictionaries()
    known = {name: {x["id"] for x in d[name]} for name in ("backgrounds", "skills", "languages")}
    tax = load_taxonomy()
    for key, m in tax["spheres"].items():
        assert set(m["backgrounds"]) <= known["backgrounds"], key
        assert set(m["skills"]) <= known["skills"], key
    assert set(tax["languages"].values()) <= known["languages"]


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
