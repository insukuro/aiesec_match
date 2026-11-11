import pytest
from fastapi.testclient import TestClient

from app.deps import get_catalog_reader
from app.main import app
from tests.factories import ListReader, make_opp


@pytest.fixture
def opps():
    return [
        make_opp(1, backgrounds={10253: "required"}, skills={10161: "required"},
                 languages={10018: "required"}),
        make_opp(2, backgrounds={99999: "required"}, languages={10018: "required"}),
        make_opp(3, kind="volunteer", languages={10018: "required"},
                 duration_weeks=6, cost_total=300.0),
    ]


@pytest.fixture
def client(opps):
    app.dependency_overrides[get_catalog_reader] = lambda: ListReader(opps)
    yield TestClient(app)
    app.dependency_overrides.clear()