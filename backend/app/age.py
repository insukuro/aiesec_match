from __future__ import annotations

from datetime import date

MIN_AGE = 16
MAX_AGE = 34  # «строго меньше 35»


def _years_between(birth: date, today: date) -> int:
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def validate_birth_date(birth: date | None, today: date | None = None) -> None:
    """Бросает ValueError с кодом 'birth_date_invalid' если:
       - дата в будущем,
       - возраст < 16,
       - возраст > 34 (т.е. строго < 35),
       - возраст > 120 (защита от опечаток).
    """
    if birth is None:
        return
    today = today or date.today()
    if birth > today:
        raise ValueError("birth_date_future")
    age = _years_between(birth, today)
    if age < MIN_AGE:
        raise ValueError("birth_date_too_young")
    if age > MAX_AGE:
        raise ValueError("birth_date_too_old")
    if age > 120:
        raise ValueError("birth_date_invalid")


def age_from_birth(birth: date | None, today: date | None = None) -> int | None:
    if birth is None:
        return None
    today = today or date.today()
    return _years_between(birth, today)


AGE_ERROR_MESSAGES = {
    "birth_date_future": "Дата рождения не может быть в будущем",
    "birth_date_too_young": f"Минимальный возраст — {MIN_AGE} лет",
    "birth_date_too_old": f"Максимальный возраст — {MAX_AGE} лет (до 35)",
    "birth_date_invalid": "Некорректная дата рождения",
}