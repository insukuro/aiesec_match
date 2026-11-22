# backend/tests/test_errors.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import (
    BadCredentials, ConsentRequired, EmailDeliveryUnavailable, EmailTaken,
    ProfileIncomplete, Problem, RateLimited, Unauthorized, Validation,
    VersionConflict, problem_handler,
)


@pytest.mark.parametrize("exc,code", [
    (Validation(), 422),
    (Unauthorized(), 401),
    (EmailTaken(), 409),
    (EmailDeliveryUnavailable(), 503),
    (BadCredentials(), 401),
    (ConsentRequired(), 409),
    (ProfileIncomplete(), 409),
    (VersionConflict(), 412),
    (RateLimited(), 429),
])
def test_status_codes(exc, code):
    assert exc.status_code == code


def test_problem_handler_shape():
    app = FastAPI()
    app.add_exception_handler(Problem, problem_handler)

    @app.get("/boom")
    async def boom():
        raise Validation(errors=[{"loc": ["body"], "msg": "bad"}])

    client = TestClient(app)
    r = client.get("/boom")
    assert r.status_code == 422
    body = r.json()
    assert body["type"] == "/problems/validation"
    assert body["errors"] == [{"loc": ["body"], "msg": "bad"}]
    assert body["instance"] == "/boom"
    assert r.headers["content-type"].startswith("application/problem+json")