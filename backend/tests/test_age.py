# backend/tests/test_age.py
from datetime import date

import pytest

from app.age import (
    AGE_ERROR_MESSAGES,
    MAX_AGE,
    MIN_AGE,
    age_from_birth,
    validate_birth_date,
)


def _birth(years_ago: int, today: date = date(2026, 11, 16)) -> date:
    # день рождения «уже прошёл» в этом году
    return date(today.year - years_ago, 1, 1)


class TestYearsBetween:
    def test_birthday_already_passed(self):
        assert age_from_birth(date(2000, 1, 1), today=date(2026, 11, 16)) == 26

    def test_birthday_not_yet(self):
        # ДР 31 декабря ещё не наступил
        assert age_from_birth(date(2000, 12, 31), today=date(2026, 11, 16)) == 25

    def test_birthday_today(self):
        assert age_from_birth(date(2000, 11, 16), today=date(2026, 11, 16)) == 26

    def test_none(self):
        assert age_from_birth(None) is None


class TestValidateBirthDate:
    def test_none_ok(self):
        validate_birth_date(None)  # не бросает

    def test_future(self):
        today = date(2026, 11, 16)
        with pytest.raises(ValueError, match="birth_date_future"):
            validate_birth_date(date(2027, 1, 1), today=today)

    def test_too_young(self):
        today = date(2026, 11, 16)
        # 15 лет
        with pytest.raises(ValueError, match="birth_date_too_young"):
            validate_birth_date(date(2011, 1, 1), today=today)

    def test_min_age_boundary_ok(self):
        today = date(2026, 11, 16)
        # ровно 16 — ок
        validate_birth_date(date(2010, 1, 1), today=today)

    def test_too_old(self):
        today = date(2026, 11, 16)
        # 35 лет (строго больше MAX_AGE=34)
        with pytest.raises(ValueError, match="birth_date_too_old"):
            validate_birth_date(date(1991, 1, 1), today=today)

    def test_max_age_boundary_ok(self):
        today = date(2026, 11, 16)
        # 34 года — ок
        validate_birth_date(date(1992, 1, 1), today=today)

    def test_error_messages_complete(self):
        assert set(AGE_ERROR_MESSAGES) == {
            "birth_date_future", "birth_date_too_young",
            "birth_date_too_old", "birth_date_invalid",
        }