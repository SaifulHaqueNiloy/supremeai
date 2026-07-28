import pytest


@pytest.fixture(autouse=True)
def override_setup_test_database():
    yield
    return