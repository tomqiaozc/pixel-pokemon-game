"""Tests for Sprint 14: Pokemon Tower event service.

These tests verify the Pokemon Tower entering, ghost blocking, Silph Scope,
Rocket battles, and Mr. Fuji rescue flow.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import create_game

client = TestClient(app)


def _create_test_game() -> str:
    game = create_game("TowerTester", 1)
    return game["id"]


# ──── Pokemon Tower State ────────────────────────────────

class TestPokemonTowerState:
    def test_initial_state(self):
        """GET /api/pokemon-tower/state/{game_id} should return initial state."""
        game_id = _create_test_game()
        resp = client.get(f"/api/pokemon-tower/state/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entered"] is False
        assert data["fuji_rescued"] is False

    def test_enter_tower(self):
        """POST /api/pokemon-tower/enter should succeed."""
        game_id = _create_test_game()
        resp = client.post("/api/pokemon-tower/enter", json={"game_id": game_id})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_ghost_blocked_without_scope(self):
        """Ghost on floor 3+ should block without Silph Scope."""
        game_id = _create_test_game()
        client.post("/api/pokemon-tower/enter", json={"game_id": game_id})
        resp = client.post("/api/pokemon-tower/ghost", json={"game_id": game_id, "floor": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("blocked") is True

    def test_floor_access_below_3(self):
        """Floors below 3 should be accessible without Silph Scope."""
        game_id = _create_test_game()
        client.post("/api/pokemon-tower/enter", json={"game_id": game_id})
        resp = client.post("/api/pokemon-tower/ghost", json={"game_id": game_id, "floor": 2})
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ──── Pokemon Tower Flow ─────────────────────────────────

class TestPokemonTowerFlow:
    def test_full_tower_flow(self):
        """enter -> ghost blocked -> scope -> rockets -> rescue Fuji."""
        game_id = _create_test_game()
        # Enter
        resp = client.post("/api/pokemon-tower/enter", json={"game_id": game_id})
        assert resp.json()["success"] is True
        # Get blocked by ghost
        resp = client.post("/api/pokemon-tower/ghost", json={"game_id": game_id, "floor": 3})
        assert resp.json().get("blocked") is True
        # Use scope
        resp = client.post("/api/pokemon-tower/scope", json={"game_id": game_id})
        assert resp.json()["success"] is True
        # Defeat rockets
        resp = client.post("/api/pokemon-tower/rockets", json={"game_id": game_id})
        assert resp.json()["success"] is True
        # Rescue Fuji
        resp = client.post("/api/pokemon-tower/rescue", json={"game_id": game_id})
        assert resp.json()["success"] is True
        assert resp.json().get("item") == "Poke Flute"

    def test_rescue_before_rockets(self):
        """POST /api/pokemon-tower/rescue before defeating rockets should fail."""
        game_id = _create_test_game()
        client.post("/api/pokemon-tower/enter", json={"game_id": game_id})
        resp = client.post("/api/pokemon-tower/rescue", json={"game_id": game_id})
        assert resp.status_code == 400

    def test_double_rescue(self):
        """Rescuing Fuji twice should return already_rescued."""
        game_id = _create_test_game()
        client.post("/api/pokemon-tower/enter", json={"game_id": game_id})
        client.post("/api/pokemon-tower/ghost", json={"game_id": game_id, "floor": 3})
        client.post("/api/pokemon-tower/scope", json={"game_id": game_id})
        client.post("/api/pokemon-tower/rockets", json={"game_id": game_id})
        client.post("/api/pokemon-tower/rescue", json={"game_id": game_id})
        resp = client.post("/api/pokemon-tower/rescue", json={"game_id": game_id})
        assert resp.status_code == 200
        assert resp.json().get("already_rescued") is True

    def test_scope_without_ghost(self):
        """POST /api/pokemon-tower/scope without ghost encounter should fail."""
        game_id = _create_test_game()
        client.post("/api/pokemon-tower/enter", json={"game_id": game_id})
        resp = client.post("/api/pokemon-tower/scope", json={"game_id": game_id})
        assert resp.status_code == 400

    def test_enter_not_entered(self):
        """POST /api/pokemon-tower/ghost without entering tower should fail."""
        game_id = _create_test_game()
        resp = client.post("/api/pokemon-tower/ghost", json={"game_id": game_id, "floor": 2})
        assert resp.status_code == 400

    def test_game_not_found(self):
        """GET /api/pokemon-tower/state/nonexistent should return 404."""
        resp = client.get("/api/pokemon-tower/state/nonexistent")
        assert resp.status_code == 404

    def test_state_after_full_flow(self):
        """State should reflect all completed steps after full flow."""
        game_id = _create_test_game()
        client.post("/api/pokemon-tower/enter", json={"game_id": game_id})
        client.post("/api/pokemon-tower/ghost", json={"game_id": game_id, "floor": 3})
        client.post("/api/pokemon-tower/scope", json={"game_id": game_id})
        client.post("/api/pokemon-tower/rockets", json={"game_id": game_id})
        client.post("/api/pokemon-tower/rescue", json={"game_id": game_id})
        resp = client.get(f"/api/pokemon-tower/state/{game_id}")
        data = resp.json()
        assert data["entered"] is True
        assert data["fuji_rescued"] is True
        assert data["rockets_defeated"] is True
