"""Shared test fixtures."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import game_service, item_service


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_game_store():
    game_service._games.clear()
    yield
    game_service._games.clear()


@pytest.fixture
def game_with_pokemon(client):
    """Create a game and return (game_id, game_state)."""
    resp = client.post("/api/game/new", json={"player_name": "Ash", "starter_pokemon_id": 4})
    assert resp.status_code == 200
    data = resp.json()
    return data["id"], data
