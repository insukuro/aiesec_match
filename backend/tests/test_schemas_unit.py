# backend/tests/test_schemas_unit.py
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import LoginIn, ProfileIn, RegisterIn


class TestRegisterIn:
    def test_ok(self):
        m = RegisterIn(email="  Foo@Bar.COM ", password="abc12345")
        assert m.email == "foo@bar.com"

    def test_short_password(self):
        with pytest.raises(ValidationError) as ei:
            RegisterIn(email="a@b.co", password="short")
        errors = ei.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_weak_password(self):
        with pytest.raises(ValidationError, match="password_weak"):
            RegisterIn(email="a@b.co", password="onlyletters")

    def test_bad_email(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="not-an-email", password="abc12345")


class TestLoginIn:
    def test_ok_and_lowercased(self):
        assert LoginIn(email="X@Y.Z", password="p").email == "x@y.z"


class TestProfileIn:
    def test_age_validation_propagates(self):
        with pytest.raises(ValidationError, match="birth_date_too_young"):
            ProfileIn(birth_date=date(2020, 1, 1))

    def test_none_birth_ok(self):
        ProfileIn(birth_date=None)

    def test_bad_english_level(self):
        with pytest.raises(ValidationError):
            ProfileIn(english_level="Z9")