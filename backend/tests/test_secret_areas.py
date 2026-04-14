"""Tests for Sprint 10: Secret Areas System."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.secret_area_service import (
    _discovered,
    _secret_areas,
    check_tile_for_secret,
    discover_area,
    get_discovered_areas,
    is_area_discovered,
    load_secret_areas,
    can_unlock_area,
)
from backend.services.game_service import create_game, get_game
from backend.services.gym_service import _earned_badges

client = TestClient(app)


# ──── Helpers ────────────────────────────────────────────────

def _create_test_game() -> str:
    """Create a game and return the game_id."""
    game = create_game("TestPlayer", 1)  # Bulbasaur
    return game["id"]


def _grant_badges(game_id: str, badge_ids: list[str]) -> None:
    """Grant badges directly for test setup."""
    if game_id not in _earned_badges:
        _earned_badges[game_id] = set()
    _earned_badges[game_id].update(badge_ids)


def _give_inventory_item(game_id: str, item_id: int) -> None:
    """Add an item to the player's inventory."""
    game = get_game(game_id)
    if game:
        game["player"].setdefault("inventory", []).append({"item_id": item_id})


def _add_team_pokemon(game_id: str, count: int) -> None:
    """Add dummy Pokemon to team until it reaches `count`."""
    game = get_game(game_id)
    if game:
        team = game["player"]["team"]
        while len(team) < count:
            team.append({
                "id": 25, "name": "Pikachu", "level": 10,
                "types": ["electric"], "moves": [],
                "current_hp": 35, "max_hp": 35,
                "stats": {"hp": 35, "attack": 55, "defense": 30,
                          "sp_attack": 50, "sp_defense": 40, "speed": 90},
            })


def _cleanup_discovered(game_id: str) -> None:
    _discovered.pop(game_id, None)


# ──── Data Loading ───────────────────────────────────────────

class TestSecretAreaDataLoading:
    def test_load_secret_areas_returns_list(self):
        areas = load_secret_areas()
        assert isinstance(areas, list)
        assert len(areas) >= 3

    def test_areas_have_required_fields(self):
        areas = load_secret_areas()
        for area in areas:
            assert area.id
            assert area.display_name
            assert area.trigger_map_id
            assert area.trigger_x is not None
            assert area.trigger_y is not None

    def test_viridian_secret_garden_exists(self):
        areas = load_secret_areas()
        garden = next((a for a in areas if a.id == "viridian_secret_garden"), None)
        assert garden is not None
        assert garden.display_name == "Viridian Secret Garden"
        assert garden.trigger_map_id == "viridian_city"
        assert garden.trigger_x == 15
        assert garden.trigger_y == 18

    def test_route_2_hidden_alcove_exists(self):
        areas = load_secret_areas()
        alcove = next((a for a in areas if a.id == "route_2_hidden_alcove"), None)
        assert alcove is not None
        assert alcove.unlock_conditions.min_badges == 1
        assert alcove.unlock_conditions.required_pokemon_count == 3


# ──── Tile Trigger Checks ────────────────────────────────────

class TestTileTriggerChecks:
    def test_normal_tile_no_trigger(self):
        game_id = _create_test_game()
        result = check_tile_for_secret(game_id, "viridian_city", 0, 0)
        assert result is None
        _cleanup_discovered(game_id)

    def test_trigger_tile_returns_area(self):
        game_id = _create_test_game()
        result = check_tile_for_secret(game_id, "viridian_city", 15, 18)
        assert result is not None
        assert result.id == "viridian_secret_garden"
        _cleanup_discovered(game_id)

    def test_wrong_map_no_trigger(self):
        game_id = _create_test_game()
        # Right coords but wrong map
        result = check_tile_for_secret(game_id, "pallet_town", 15, 18)
        assert result is None
        _cleanup_discovered(game_id)

    def test_multiple_areas_different_maps(self):
        game_id = _create_test_game()
        r1 = check_tile_for_secret(game_id, "viridian_city", 15, 18)
        r2 = check_tile_for_secret(game_id, "route_2", 5, 28)
        assert r1 is not None and r1.id == "viridian_secret_garden"
        assert r2 is not None and r2.id == "route_2_hidden_alcove"
        _cleanup_discovered(game_id)


# ──── Unlock Conditions ──────────────────────────────────────

class TestUnlockConditions:
    def test_no_conditions_can_unlock(self):
        game_id = _create_test_game()
        areas = load_secret_areas()
        garden = next(a for a in areas if a.id == "viridian_secret_garden")
        assert can_unlock_area(game_id, garden) is True
        _cleanup_discovered(game_id)

    def test_badge_requirement_unmet(self):
        game_id = _create_test_game()
        areas = load_secret_areas()
        alcove = next(a for a in areas if a.id == "route_2_hidden_alcove")
        # No badges = cannot unlock (needs 1)
        assert can_unlock_area(game_id, alcove) is False
        _cleanup_discovered(game_id)

    def test_badge_requirement_met(self):
        game_id = _create_test_game()
        _grant_badges(game_id, ["boulder"])
        _add_team_pokemon(game_id, 3)
        areas = load_secret_areas()
        alcove = next(a for a in areas if a.id == "route_2_hidden_alcove")
        assert can_unlock_area(game_id, alcove) is True
        _cleanup_discovered(game_id)

    def test_item_requirement_unmet(self):
        game_id = _create_test_game()
        _grant_badges(game_id, ["boulder"])
        areas = load_secret_areas()
        underground = next(a for a in areas if a.id == "pewter_city_underground")
        assert can_unlock_area(game_id, underground) is False
        _cleanup_discovered(game_id)

    def test_item_requirement_met(self):
        game_id = _create_test_game()
        _grant_badges(game_id, ["boulder"])
        _give_inventory_item(game_id, 15)
        areas = load_secret_areas()
        underground = next(a for a in areas if a.id == "pewter_city_underground")
        assert can_unlock_area(game_id, underground) is True
        _cleanup_discovered(game_id)

    def test_pokemon_count_requirement_unmet(self):
        game_id = _create_test_game()
        _grant_badges(game_id, ["boulder"])
        areas = load_secret_areas()
        alcove = next(a for a in areas if a.id == "route_2_hidden_alcove")
        # Only 1 Pokemon in team, needs 3
        assert can_unlock_area(game_id, alcove) is False
        _cleanup_discovered(game_id)

    def test_invalid_game_id_cannot_unlock(self):
        areas = load_secret_areas()
        garden = next(a for a in areas if a.id == "viridian_secret_garden")
        assert can_unlock_area("nonexistent_game", garden) is False


# ──── Discovery Flow ─────────────────────────────────────────

class TestDiscoveryFlow:
    def test_discover_area_success(self):
        game_id = _create_test_game()
        result = discover_area(game_id, "viridian_secret_garden")
        assert result is not None
        assert result.discovered is True
        assert result.area_id == "viridian_secret_garden"
        assert result.display_name == "Viridian Secret Garden"
        _cleanup_discovered(game_id)

    def test_discover_already_discovered_idempotent(self):
        game_id = _create_test_game()
        discover_area(game_id, "viridian_secret_garden")
        result = discover_area(game_id, "viridian_secret_garden")
        assert result is not None
        assert result.discovered is True
        assert "already" in result.message.lower()
        _cleanup_discovered(game_id)

    def test_discover_unmet_conditions(self):
        game_id = _create_test_game()
        result = discover_area(game_id, "route_2_hidden_alcove")
        assert result is not None
        assert result.discovered is False
        assert "requirements" in result.message.lower()
        _cleanup_discovered(game_id)

    def test_discover_invalid_game(self):
        result = discover_area("nonexistent_game", "viridian_secret_garden")
        assert result is None

    def test_discover_invalid_area(self):
        game_id = _create_test_game()
        result = discover_area(game_id, "nonexistent_area")
        assert result is None
        _cleanup_discovered(game_id)

    def test_rewards_grant_experience(self):
        game_id = _create_test_game()
        game = get_game(game_id)
        initial_exp = game["player"]["team"][0].get("experience", 0)
        discover_area(game_id, "viridian_secret_garden")
        new_exp = game["player"]["team"][0].get("experience", 0)
        assert new_exp > initial_exp
        assert new_exp - initial_exp == 100  # Viridian garden grants 100 XP
        _cleanup_discovered(game_id)


# ──── Progress Tracking ──────────────────────────────────────

class TestProgressTracking:
    def test_empty_progress(self):
        game_id = _create_test_game()
        discovered = get_discovered_areas(game_id)
        assert discovered == []
        _cleanup_discovered(game_id)

    def test_progress_after_discovery(self):
        game_id = _create_test_game()
        discover_area(game_id, "viridian_secret_garden")
        discovered = get_discovered_areas(game_id)
        assert "viridian_secret_garden" in discovered
        _cleanup_discovered(game_id)

    def test_is_area_discovered_true(self):
        game_id = _create_test_game()
        discover_area(game_id, "viridian_secret_garden")
        assert is_area_discovered(game_id, "viridian_secret_garden") is True
        _cleanup_discovered(game_id)

    def test_is_area_discovered_false(self):
        game_id = _create_test_game()
        assert is_area_discovered(game_id, "viridian_secret_garden") is False
        _cleanup_discovered(game_id)


# ──── API Endpoint Integration ───────────────────────────────

class TestSecretAreaEndpoints:
    def test_list_areas_endpoint(self):
        resp = client.get("/api/secret/areas")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_check_secret_no_trigger(self):
        game_id = _create_test_game()
        resp = client.post("/api/secret/check", json={
            "game_id": game_id, "map_id": "viridian_city", "x": 0, "y": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["discovered"] is False
        _cleanup_discovered(game_id)

    def test_check_secret_trigger_found(self):
        game_id = _create_test_game()
        resp = client.post("/api/secret/check", json={
            "game_id": game_id, "map_id": "viridian_city", "x": 15, "y": 18,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["discovered"] is True
        assert data["area_id"] == "viridian_secret_garden"
        _cleanup_discovered(game_id)

    def test_check_secret_invalid_game(self):
        resp = client.post("/api/secret/check", json={
            "game_id": "bad_id", "map_id": "viridian_city", "x": 15, "y": 18,
        })
        assert resp.status_code == 404

    def test_discover_endpoint_success(self):
        game_id = _create_test_game()
        resp = client.post("/api/secret/discover", json={
            "game_id": game_id, "map_id": "viridian_city", "x": 15, "y": 18,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["discovered"] is True
        assert data["area_id"] == "viridian_secret_garden"
        _cleanup_discovered(game_id)

    def test_discover_endpoint_no_area(self):
        game_id = _create_test_game()
        resp = client.post("/api/secret/discover", json={
            "game_id": game_id, "map_id": "viridian_city", "x": 0, "y": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["discovered"] is False
        _cleanup_discovered(game_id)

    def test_progress_endpoint_empty(self):
        game_id = _create_test_game()
        resp = client.get(f"/api/secret/progress/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["discovered_areas"] == []
        _cleanup_discovered(game_id)

    def test_progress_endpoint_after_discover(self):
        game_id = _create_test_game()
        client.post("/api/secret/discover", json={
            "game_id": game_id, "map_id": "viridian_city", "x": 15, "y": 18,
        })
        resp = client.get(f"/api/secret/progress/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "viridian_secret_garden" in data["discovered_areas"]
        _cleanup_discovered(game_id)

    def test_progress_endpoint_invalid_game(self):
        resp = client.get("/api/secret/progress/bad_id")
        assert resp.status_code == 404
