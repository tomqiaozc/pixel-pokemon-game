"""Shared test fixtures."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import game_service


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_game_store():
    game_service._games.clear()
    yield
    game_service._games.clear()
