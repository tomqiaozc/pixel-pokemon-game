"""Tests for Sprint 13 QA: Lt. Surge trash can puzzle and Vermilion Gym."""
from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import create_game
from backend.services.trash_can_puzzle_service import _puzzle_state, _init_puzzle

client = TestClient(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def _create_test_game() -> str:
    game = create_game("SurgeTester", 1)
    return game["id"]


# ──── Trash Can Puzzle State ───────────────────────────────

class TestTrashCanPuzzleState:
    def test_puzzle_initial_state(self):
        game_id = _create_test_game()
        resp = client.get(f"/api/trash-puzzle/state/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["solved"] is False
        assert data["first_found"] is False
        assert data["checked_cans"] == []

    def test_check_empty_can(self):
        game_id = _create_test_game()
        # Force switch positions so we know which cans are empty
        _puzzle_state[game_id] = {
            "switch_positions": [3, 7],
            "first_found": False,
            "first_can": None,
            "solved": False,
            "checked_cans": [],
        }
        resp = client.post("/api/trash-puzzle/check", json={
            "game_id": game_id,
            "can_index": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "empty"

    def test_puzzle_reset(self):
        game_id = _create_test_game()
        resp = client.post("/api/trash-puzzle/reset", json={"game_id": game_id})
        assert resp.status_code == 200
        resp = client.get(f"/api/trash-puzzle/state/{game_id}")
        data = resp.json()
        assert data["solved"] is False
        assert data["first_found"] is False


# ──── Trash Can Puzzle Flow ────────────────────────────────

class TestTrashCanPuzzleFlow:
    def _setup_puzzle(self, game_id, switches=(3, 7)):
        _puzzle_state[game_id] = {
            "switch_positions": list(switches),
            "first_found": False,
            "first_can": None,
            "solved": False,
            "checked_cans": [],
        }

    def test_find_first_switch(self):
        game_id = _create_test_game()
        self._setup_puzzle(game_id, switches=(3, 7))
        resp = client.post("/api/trash-puzzle/check", json={
            "game_id": game_id,
            "can_index": 3,
        })
        assert resp.status_code == 200
        assert resp.json()["result"] == "first_switch"

    def test_find_second_switch_solves(self):
        game_id = _create_test_game()
        self._setup_puzzle(game_id, switches=(3, 7))
        client.post("/api/trash-puzzle/check", json={"game_id": game_id, "can_index": 3})
        resp = client.post("/api/trash-puzzle/check", json={"game_id": game_id, "can_index": 7})
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "second_switch"
        assert data["solved"] is True

    def test_wrong_second_resets(self):
        game_id = _create_test_game()
        self._setup_puzzle(game_id, switches=(3, 7))
        client.post("/api/trash-puzzle/check", json={"game_id": game_id, "can_index": 3})
        resp = client.post("/api/trash-puzzle/check", json={"game_id": game_id, "can_index": 0})
        assert resp.status_code == 200
        assert resp.json()["result"] == "wrong_reset"
        state_resp = client.get(f"/api/trash-puzzle/state/{game_id}")
        assert state_resp.json()["first_found"] is False

    def test_already_solved(self):
        game_id = _create_test_game()
        self._setup_puzzle(game_id, switches=(3, 7))
        client.post("/api/trash-puzzle/check", json={"game_id": game_id, "can_index": 3})
        client.post("/api/trash-puzzle/check", json={"game_id": game_id, "can_index": 7})
        resp = client.post("/api/trash-puzzle/check", json={"game_id": game_id, "can_index": 0})
        assert resp.json()["result"] == "already_solved"


# ──── Vermilion Gym Data ───────────────────────────────────

class TestVermilionGymData:
    def test_vermilion_gym_exists(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "vermilion_gym"), None)
        assert gym is not None

    def test_vermilion_gym_badge(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "vermilion_gym"), None)
        assert gym["badge_name"] == "Thunder Badge"

    def test_vermilion_gym_leader(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "vermilion_gym"), None)
        assert gym["leader"]["name"] == "Lt. Surge"

    def test_vermilion_gym_type(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "vermilion_gym"), None)
        assert gym["type_specialty"] == "electric"

    def test_vermilion_leader_team(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "vermilion_gym"), None)
        team = gym["leader"]["pokemon_team"]
        assert len(team) == 3
        names = [p["name"] for p in team]
        assert "Raichu" in names
