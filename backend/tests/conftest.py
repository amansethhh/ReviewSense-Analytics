"""Shared test fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """
    Create a TestClient that triggers lifespan events.
    This ensures load_artifacts() runs before any tests.
    """
    with TestClient(app) as c:
        yield c
