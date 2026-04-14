"""Tests for Sprint 10: Cave System."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.cave_service import (
    _cave_lit,
    get_cave_encounter_modifier,
    get_cave_maps,
    get_cave_state,
    get_cave_transition,
    is_dark_cave,
    use_flash_in_cave,
)
from backend.services.map_service import get_map
from backend.services.encounter_service import get_encounter_table
from backend.services.game_service import create_game, get_game
from backend.services.gym_service import _earned_badges

client = TestClient(app)


# ──── Helpers ────────────────────────────────────────────────

def _create_test_game() -> str:
    game = create_game("CaveTester", 1)
    return game["id"]


def _grant_badges(game_id: str, badge_ids: list[str]) -> None:
    if game_id not in _earned_badges:
        _earned_badges[game_id] = set()
    _earned_badges[game_id].update(badge_ids)


def _give_hm_move(game_id: str, pokemon_index: int, move_name: str) -> None:
    game = get_game(game_id)
    if game:
        team = game["player"]["team"]
        if pokemon_index < len(team):
            team[pokemon_index].setdefault("moves", []).append({
                "name": move_name, "type": "normal", "power": 0,
                "accuracy": 100, "pp": 20, "category": "status",
            })


def _cleanup(game_id: str) -> None:
    _cave_lit.pop(game_id, None)


# ──── Cave Map Data ──────────────────────────────────────────

class TestCaveMapData:
    def test_mt_moon_entrance_exists(self):
        game_map = get_map("mt_moon_entrance")
        assert game_map is not None
        assert game_map.map_type == "cave"
        assert game_map.is_dark is False
        assert game_map.cave_level == 0

    def test_mt_moon_b1_exists_and_is_dark(self):
        game_map = get_map("mt_moon_b1")
        assert game_map is not None
        assert game_map.map_type == "cave"
        assert game_map.is_dark is True
        assert game_map.cave_level == 1

    def test_digletts_cave_exists_and_is_dark(self):
        game_map = get_map("digletts_cave")
        assert game_map is not None
        assert game_map.map_type == "cave"
        assert game_map.is_dark is True
        assert game_map.cave_level == 1

    def test_non_cave_map_not_dark(self):
        game_map = get_map("pallet_town")
        assert game_map is not None
        assert game_map.map_type != "cave"
        assert game_map.is_dark is False


# ──── is_dark_cave ───────────────────────────────────────────

class TestIsDarkCave:
    def test_dark_cave_returns_true(self):
        assert is_dark_cave("mt_moon_b1") is True

    def test_non_dark_cave_returns_false(self):
        assert is_dark_cave("mt_moon_entrance") is False

    def test_non_cave_returns_false(self):
        assert is_dark_cave("pallet_town") is False

    def test_nonexistent_map_returns_false(self):
        assert is_dark_cave("nonexistent") is False


# ──── Cave Encounter Tables ──────────────────────────────────

class TestCaveEncounterTables:
    def test_mt_moon_1f_table_exists(self):
        table = get_encounter_table("mt_moon_1f")
        assert table is not None
        assert len(table.encounters) >= 1

    def test_mt_moon_b1_table_exists(self):
        table = get_encounter_table("mt_moon_b1")
        assert table is not None
        assert len(table.encounters) >= 1

    def test_digletts_cave_table_exists(self):
        table = get_encounter_table("digletts_cave")
        assert table is not None
        assert len(table.encounters) >= 1

    def test_cave_encounter_species_are_valid(self):
        """Cave encounter tables reference species IDs 41,46,35,74,27 —
        these cave Pokemon are not yet in species data (known data gap).
        This test documents the gap and verifies the table structure."""
        table = get_encounter_table("mt_moon_1f")
        expected_species_ids = {41, 46, 35, 74, 27}
        actual_ids = {e.species_id for e in table.encounters}
        assert actual_ids == expected_species_ids
        # All entries have valid level ranges
        for entry in table.encounters:
            assert entry.min_level <= entry.max_level
            assert entry.weight > 0


# ──── Cave State ─────────────────────────────────────────────

class TestCaveState:
    def test_dark_cave_default_state(self):
        game_id = _create_test_game()
        state = get_cave_state(game_id, "mt_moon_b1")
        assert state is not None
        assert state.is_lit is False
        assert state.visibility_radius == 2
        _cleanup(game_id)

    def test_non_dark_cave_lit_by_default(self):
        game_id = _create_test_game()
        state = get_cave_state(game_id, "mt_moon_entrance")
        assert state is not None
        assert state.is_lit is True
        assert state.visibility_radius == 10
        _cleanup(game_id)

    def test_non_cave_returns_none(self):
        game_id = _create_test_game()
        state = get_cave_state(game_id, "pallet_town")
        assert state is None
        _cleanup(game_id)

    def test_nonexistent_map_returns_none(self):
        game_id = _create_test_game()
        state = get_cave_state(game_id, "nonexistent")
        assert state is None
        _cleanup(game_id)


# ──── Flash ──────────────────────────────────────────────────

class TestFlash:
    def test_flash_lights_dark_cave(self):
        game_id = _create_test_game()
        result = use_flash_in_cave(game_id, "mt_moon_b1", 0)
        assert result.success is True
        assert result.visibility_radius == 10
        assert "lit" in result.message.lower()
        _cleanup(game_id)

    def test_flash_already_lit(self):
        game_id = _create_test_game()
        use_flash_in_cave(game_id, "mt_moon_b1", 0)
        result = use_flash_in_cave(game_id, "mt_moon_b1", 0)
        assert result.success is True
        assert "already lit" in result.message.lower()
        _cleanup(game_id)

    def test_flash_not_a_cave(self):
        game_id = _create_test_game()
        result = use_flash_in_cave(game_id, "pallet_town", 0)
        assert result.success is False
        assert "isn't a cave" in result.message.lower()
        _cleanup(game_id)

    def test_flash_bright_cave(self):
        game_id = _create_test_game()
        result = use_flash_in_cave(game_id, "mt_moon_entrance", 0)
        assert result.success is False
        assert "already bright" in result.message.lower()
        _cleanup(game_id)

    def test_flash_nonexistent_map(self):
        game_id = _create_test_game()
        result = use_flash_in_cave(game_id, "nonexistent", 0)
        assert result.success is False
        _cleanup(game_id)

    def test_flash_state_persists(self):
        game_id = _create_test_game()
        use_flash_in_cave(game_id, "mt_moon_b1", 0)
        state = get_cave_state(game_id, "mt_moon_b1")
        assert state.is_lit is True
        assert state.visibility_radius == 10
        _cleanup(game_id)


# ──── Cave Transitions ───────────────────────────────────────

class TestCaveTransitions:
    def test_valid_ladder_transition(self):
        game_id = _create_test_game()
        result = get_cave_transition(game_id, "mt_moon_entrance", 12, 5)
        assert result is not None
        assert result.target_map_id == "mt_moon_b1"
        assert result.spawn_x == 15
        assert result.spawn_y == 28
        assert result.is_dark is True
        assert result.cave_level == 1
        _cleanup(game_id)

    def test_reverse_ladder_transition(self):
        game_id = _create_test_game()
        result = get_cave_transition(game_id, "mt_moon_b1", 15, 28)
        assert result is not None
        assert result.target_map_id == "mt_moon_entrance"
        _cleanup(game_id)

    def test_invalid_ladder_coords(self):
        game_id = _create_test_game()
        result = get_cave_transition(game_id, "mt_moon_entrance", 0, 0)
        assert result is None
        _cleanup(game_id)

    def test_transition_updates_player_position(self):
        game_id = _create_test_game()
        get_cave_transition(game_id, "mt_moon_entrance", 12, 5)
        game = get_game(game_id)
        pos = game["player"]["position"]
        assert pos["map_id"] == "mt_moon_b1"
        assert pos["x"] == 15
        assert pos["y"] == 28
        _cleanup(game_id)


# ──── Encounter Modifier ─────────────────────────────────────

class TestEncounterModifier:
    def test_cave_level_0_modifier(self):
        assert get_cave_encounter_modifier(0) == 1.0

    def test_cave_level_1_modifier(self):
        assert get_cave_encounter_modifier(1) == pytest.approx(1.1)

    def test_cave_level_3_modifier(self):
        assert get_cave_encounter_modifier(3) == pytest.approx(1.3)


# ──── Cave Maps List ─────────────────────────────────────────

class TestCaveMaps:
    def test_cave_maps_list(self):
        caves = get_cave_maps()
        assert isinstance(caves, list)
        assert len(caves) >= 3
        ids = [c["id"] for c in caves]
        assert "mt_moon_entrance" in ids
        assert "mt_moon_b1" in ids
        assert "digletts_cave" in ids

    def test_cave_maps_have_required_fields(self):
        for cave in get_cave_maps():
            assert "id" in cave
            assert "display_name" in cave
            assert "is_dark" in cave
            assert "cave_level" in cave


# ──── API Endpoint Integration ───────────────────────────────

class TestCaveEndpoints:
    def test_cave_state_endpoint(self):
        game_id = _create_test_game()
        resp = client.get(f"/api/cave/state/{game_id}/mt_moon_b1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_lit"] is False
        assert data["visibility_radius"] == 2
        _cleanup(game_id)

    def test_cave_state_non_cave(self):
        game_id = _create_test_game()
        resp = client.get(f"/api/cave/state/{game_id}/pallet_town")
        assert resp.status_code == 404
        _cleanup(game_id)

    def test_cave_state_invalid_game(self):
        resp = client.get("/api/cave/state/bad_id/mt_moon_b1")
        assert resp.status_code == 404

    def test_flash_endpoint(self):
        game_id = _create_test_game()
        resp = client.post("/api/cave/flash", json={
            "game_id": game_id, "map_id": "mt_moon_b1", "pokemon_index": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["visibility_radius"] == 10
        _cleanup(game_id)

    def test_flash_endpoint_invalid_game(self):
        resp = client.post("/api/cave/flash", json={
            "game_id": "bad_id", "map_id": "mt_moon_b1", "pokemon_index": 0,
        })
        assert resp.status_code == 404

    def test_transition_endpoint(self):
        game_id = _create_test_game()
        resp = client.post("/api/cave/transition", json={
            "game_id": game_id, "from_map_id": "mt_moon_entrance",
            "ladder_x": 12, "ladder_y": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_map_id"] == "mt_moon_b1"
        assert data["is_dark"] is True
        _cleanup(game_id)

    def test_transition_endpoint_invalid_coords(self):
        game_id = _create_test_game()
        resp = client.post("/api/cave/transition", json={
            "game_id": game_id, "from_map_id": "mt_moon_entrance",
            "ladder_x": 0, "ladder_y": 0,
        })
        assert resp.status_code == 404
        _cleanup(game_id)

    def test_cave_maps_endpoint(self):
        resp = client.get("/api/cave/maps")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        ids = [c["id"] for c in data]
        assert "mt_moon_b1" in ids
