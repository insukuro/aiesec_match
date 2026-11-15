# backend/tests/test_completeness.py
import pytest

from app.completeness import CHECK_FIELDS, completeness, missing_for_match


FULL = {
    "programmes": ["talent"],
    "english_level": "B2",
    "study": {"status": "bachelor"},
    "work_experience": "1_2_years",
    "spheres": ["it"],
    "desired_countries": ["TR"],
    "duration": {"min_weeks": 6},
    "start_window": "asap",
    "motivation_text": "хочу",
}


def test_full_is_one():
    assert completeness(FULL) == 1.0


def test_empty_is_zero():
    assert completeness({}) == 0.0


def test_activities_count_as_spheres():
    b = dict(FULL)
    b.pop("spheres")
    b["activities"] = ["teaching"]
    assert completeness(b) == 1.0


def test_duration_max_only():
    b = dict(FULL)
    b["duration"] = {"max_weeks": 12}
    assert completeness(b) == 1.0


def test_partial_rounded():
    b = {"programmes": ["talent"], "english_level": "B2"}
    # 2 / 9
    assert completeness(b) == pytest.approx(0.222)


def test_missing_for_match_empty_when_full():
    full = {**FULL, "birth_date": "2000-01-01"}
    assert missing_for_match(full) == []


def test_missing_for_match_lists_all():
    miss = missing_for_match({})
    assert set(miss) == {"english_level", "study.status", "birth_date", "programmes"}


def test_missing_programmes_ok_if_spheres():
    b = {"english_level": "B2", "study": {"status": "bachelor"},
         "birth_date": "2000-01-01", "spheres": ["it"]}
    assert missing_for_match(b) == []