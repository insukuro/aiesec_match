import pytest
from fastapi.testclient import TestClient

from app.deps import get_catalog_reader
from app.main import app
from tests.factories import ListReader, make_opp

# ---------- уровни тестирования (Коцур, лекция 1: smoke / critical path / extended) ----------
# Уровень назначается здесь, в одном месте, чтобы не править каждый тест.
SMOKE = {"test_health", "test_match_ok", "test_dictionary"}
CRITICAL_FILES = {"test_api.py", "test_filters.py", "test_scoring.py", "test_router.py",
                  "test_contract.py", "test_spec_values.py"}


def pytest_collection_modifyitems(items):
    for item in items:
        name = item.originalname if hasattr(item, "originalname") and item.originalname else item.name
        fname = item.path.name
        if name in SMOKE:
            item.add_marker(pytest.mark.smoke)
        elif fname in CRITICAL_FILES:
            item.add_marker(pytest.mark.critical)
        else:
            item.add_marker(pytest.mark.extended)
        if fname == "test_regression_bugs.py":
            item.add_marker(pytest.mark.regression)


# ---------- фикстуры ----------
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


@pytest.fixture
def make_client():
    """Клиент с произвольным каталогом: make_client([make_opp(...), ...])."""
    def _make(opps, raise_server_exceptions=False):
        app.dependency_overrides[get_catalog_reader] = lambda: ListReader(opps)
        return TestClient(app, raise_server_exceptions=raise_server_exceptions)
    yield _make
    app.dependency_overrides.clear()
