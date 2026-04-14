"""Tests for Sprint 10: HM Overworld System."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.hm_overworld_service import (
    _boulder_positions,
    _boulder_push_counts,
    _removed_obstacles,
    _strength_active,
    _surf_state,
    can_use_hm,
    exit_surf,
    get_obstacle_states,
    get_obstacles_for_map,
    get_removed_obstacles,
    get_surf_state,
    load_hm_obstacles,
    push_boulder,
    use_cut,
    use_flash,
    use_strength,
    use_surf,
)
from backend.services.game_service import create_game, get_game
from backend.services.gym_service import _earned_badges

client = TestClient(app)


# ──── Helpers ────────────────────────────────────────────────

def _create_test_game() -> str:
    game = create_game("HMTester", 1)
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
                "name": move_name, "type": "normal", "power": 50,
                "accuracy": 95, "pp": 30, "category": "physical",
            })


def _cleanup(game_id: str) -> None:
    _removed_obstacles.pop(game_id, None)
    _surf_state.pop(game_id, None)
    _strength_active.pop(game_id, None)
    _boulder_positions.pop(game_id, None)
    _boulder_push_counts.pop(game_id, None)


# ──── Obstacle Data Loading ──────────────────────────────────

class TestObstacleLoading:
    def test_load_obstacles_returns_list(self):
        obstacles = load_hm_obstacles()
        assert isinstance(obstacles, list)
        assert len(obstacles) >= 7

    def test_obstacles_have_required_fields(self):
        for obs in load_hm_obstacles():
            assert obs.id
            assert obs.map_id
            assert obs.obstacle_type in ("cuttable_tree", "pushable_boulder", "surf_zone")
            assert obs.hm_required in ("Cut", "Surf", "Strength", "Flash")

    def test_get_obstacles_for_route_1(self):
        obstacles = get_obstacles_for_map("route_1")
        assert len(obstacles) >= 1
        assert all(o.map_id == "route_1" for o in obstacles)

    def test_get_obstacles_for_unknown_map(self):
        obstacles = get_obstacles_for_map("nonexistent_map")
        assert obstacles == []

    def test_route_2_has_tree_and_boulder(self):
        obstacles = get_obstacles_for_map("route_2")
        types = {o.obstacle_type for o in obstacles}
        assert "cuttable_tree" in types
        assert "pushable_boulder" in types


# ──── HM Permission Checks ──────────────────────────────────

class TestCanUseHM:
    def test_no_move_fails(self):
        game_id = _create_test_game()
        can, msg = can_use_hm(game_id, "Cut", 0)
        assert can is False
        assert "doesn't know" in msg.lower()
        _cleanup(game_id)

    def test_no_badge_fails(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        can, msg = can_use_hm(game_id, "Cut", 0)
        assert can is False
        assert "badge" in msg.lower()
        _cleanup(game_id)

    def test_with_move_and_badge_succeeds(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        _grant_badges(game_id, ["cascade"])
        can, msg = can_use_hm(game_id, "Cut", 0)
        assert can is True
        assert msg == "OK"
        _cleanup(game_id)

    def test_invalid_game_id(self):
        can, msg = can_use_hm("nonexistent", "Cut", 0)
        assert can is False
        assert "not found" in msg.lower()


# ──── Cut ────────────────────────────────────────────────────

class TestUseCut:
    def test_cut_success(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        _grant_badges(game_id, ["cascade"])
        result = use_cut(game_id, "route_1", 8, 12, 0)
        assert result.success is True
        assert result.effect == "tree_removed"
        assert result.obstacle_id == "route_1_tree_1"
        _cleanup(game_id)

    def test_cut_no_move(self):
        game_id = _create_test_game()
        result = use_cut(game_id, "route_1", 8, 12, 0)
        assert result.success is False
        _cleanup(game_id)

    def test_cut_no_badge(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        result = use_cut(game_id, "route_1", 8, 12, 0)
        assert result.success is False
        assert "badge" in result.message.lower()
        _cleanup(game_id)

    def test_cut_wrong_target(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        _grant_badges(game_id, ["cascade"])
        result = use_cut(game_id, "route_1", 0, 0, 0)
        assert result.success is False
        assert "nothing to cut" in result.message.lower()
        _cleanup(game_id)

    def test_cut_already_removed(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        _grant_badges(game_id, ["cascade"])
        use_cut(game_id, "route_1", 8, 12, 0)
        result = use_cut(game_id, "route_1", 8, 12, 0)
        assert result.success is True
        assert result.effect == "already_removed"
        _cleanup(game_id)

    def test_removed_obstacles_tracked(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        _grant_badges(game_id, ["cascade"])
        use_cut(game_id, "route_1", 8, 12, 0)
        removed = get_removed_obstacles(game_id, "route_1")
        assert "route_1_tree_1" in removed
        _cleanup(game_id)


# ──── Strength ───────────────────────────────────────────────

class TestUseStrength:
    def test_strength_success(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Strength")
        _grant_badges(game_id, ["rainbow"])
        result = use_strength(game_id, "route_2", 14, 10, 0)
        assert result.success is True
        assert result.effect == "strength_activated"
        _cleanup(game_id)

    def test_strength_no_boulder(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Strength")
        _grant_badges(game_id, ["rainbow"])
        result = use_strength(game_id, "route_2", 0, 0, 0)
        assert result.success is False
        assert "no boulder" in result.message.lower()
        _cleanup(game_id)

    def test_push_boulder_success(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Strength")
        _grant_badges(game_id, ["rainbow"])
        use_strength(game_id, "route_2", 14, 10, 0)
        result = push_boulder(game_id, "route_2_boulder_1", "right")
        assert result.success is True
        assert result.new_x == 15
        assert result.new_y == 10
        _cleanup(game_id)

    def test_push_boulder_without_strength_active(self):
        game_id = _create_test_game()
        result = push_boulder(game_id, "route_2_boulder_1", "right")
        assert result.success is False
        assert "strength first" in result.message.lower()
        _cleanup(game_id)

    def test_push_boulder_up(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Strength")
        _grant_badges(game_id, ["rainbow"])
        use_strength(game_id, "route_2", 14, 10, 0)
        result = push_boulder(game_id, "route_2_boulder_1", "up")
        assert result.success is True
        assert result.new_y == 9
        _cleanup(game_id)

    def test_push_limit_exceeded(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Strength")
        _grant_badges(game_id, ["rainbow"])
        use_strength(game_id, "route_2", 14, 10, 0)
        # route_2_boulder_1 has push_limit=5
        for _ in range(5):
            push_boulder(game_id, "route_2_boulder_1", "right")
        result = push_boulder(game_id, "route_2_boulder_1", "right")
        assert result.success is False
        assert "can't be pushed" in result.message.lower()
        _cleanup(game_id)

    def test_push_invalid_direction(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Strength")
        _grant_badges(game_id, ["rainbow"])
        use_strength(game_id, "route_2", 14, 10, 0)
        result = push_boulder(game_id, "route_2_boulder_1", "diagonal")
        assert result.success is False
        assert "invalid direction" in result.message.lower()
        _cleanup(game_id)


# ──── Surf ───────────────────────────────────────────────────

class TestUseSurf:
    def test_surf_success(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Surf")
        _grant_badges(game_id, ["soul"])
        result = use_surf(game_id, "pallet_town", 11, 15, 0)
        assert result.success is True
        assert result.effect == "surfing_started"
        assert result.new_state["surfing"] is True
        _cleanup(game_id)

    def test_surf_no_water(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Surf")
        _grant_badges(game_id, ["soul"])
        result = use_surf(game_id, "pallet_town", 0, 0, 0)
        assert result.success is False
        assert "no water" in result.message.lower()
        _cleanup(game_id)

    def test_surf_state_persists(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Surf")
        _grant_badges(game_id, ["soul"])
        use_surf(game_id, "pallet_town", 11, 15, 0)
        assert get_surf_state(game_id) is True
        _cleanup(game_id)

    def test_exit_surf(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Surf")
        _grant_badges(game_id, ["soul"])
        use_surf(game_id, "pallet_town", 11, 15, 0)
        result = exit_surf(game_id)
        assert result is True
        assert get_surf_state(game_id) is False
        _cleanup(game_id)

    def test_exit_surf_when_not_surfing(self):
        game_id = _create_test_game()
        result = exit_surf(game_id)
        assert result is False
        _cleanup(game_id)


# ──── Flash (delegates to cave) ──────────────────────────────

class TestUseFlash:
    def test_flash_no_move(self):
        game_id = _create_test_game()
        result = use_flash(game_id, "mt_moon_b1", 0)
        assert result.success is False
        _cleanup(game_id)

    def test_flash_no_badge(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Flash")
        result = use_flash(game_id, "mt_moon_b1", 0)
        assert result.success is False
        assert "badge" in result.message.lower()
        _cleanup(game_id)


# ──── State Isolation ────────────────────────────────────────

class TestStateIsolation:
    def test_different_games_independent_cut(self):
        game_id_1 = _create_test_game()
        game_id_2 = _create_test_game()
        _give_hm_move(game_id_1, 0, "Cut")
        _give_hm_move(game_id_2, 0, "Cut")
        _grant_badges(game_id_1, ["cascade"])
        _grant_badges(game_id_2, ["cascade"])
        use_cut(game_id_1, "route_1", 8, 12, 0)
        removed_1 = get_removed_obstacles(game_id_1, "route_1")
        removed_2 = get_removed_obstacles(game_id_2, "route_1")
        assert "route_1_tree_1" in removed_1
        assert "route_1_tree_1" not in removed_2
        _cleanup(game_id_1)
        _cleanup(game_id_2)

    def test_different_games_independent_surf(self):
        game_id_1 = _create_test_game()
        game_id_2 = _create_test_game()
        _give_hm_move(game_id_1, 0, "Surf")
        _grant_badges(game_id_1, ["soul"])
        use_surf(game_id_1, "pallet_town", 11, 15, 0)
        assert get_surf_state(game_id_1) is True
        assert get_surf_state(game_id_2) is False
        _cleanup(game_id_1)
        _cleanup(game_id_2)


# ──── Obstacle State Endpoint ────────────────────────────────

class TestObstacleStates:
    def test_obstacle_states_initial(self):
        game_id = _create_test_game()
        states = get_obstacle_states(game_id, "route_1")
        assert len(states) >= 1
        for state in states:
            assert state["removed"] is False
        _cleanup(game_id)

    def test_obstacle_states_after_cut(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        _grant_badges(game_id, ["cascade"])
        use_cut(game_id, "route_1", 8, 12, 0)
        states = get_obstacle_states(game_id, "route_1")
        tree = next(s for s in states if s["id"] == "route_1_tree_1")
        assert tree["removed"] is True
        _cleanup(game_id)


# ──── API Endpoint Integration ───────────────────────────────

class TestHMEndpoints:
    def test_use_hm_endpoint_cut(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Cut")
        _grant_badges(game_id, ["cascade"])
        resp = client.post("/api/hm/use", json={
            "game_id": game_id, "hm_move": "Cut", "map_id": "route_1",
            "target_x": 8, "target_y": 12, "pokemon_index": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["effect"] == "tree_removed"
        _cleanup(game_id)

    def test_use_hm_endpoint_invalid_game(self):
        resp = client.post("/api/hm/use", json={
            "game_id": "bad_id", "hm_move": "Cut", "map_id": "route_1",
            "target_x": 8, "target_y": 12, "pokemon_index": 0,
        })
        assert resp.status_code == 404

    def test_use_hm_endpoint_unknown_move(self):
        game_id = _create_test_game()
        resp = client.post("/api/hm/use", json={
            "game_id": game_id, "hm_move": "Fly", "map_id": "route_1",
            "target_x": 8, "target_y": 12, "pokemon_index": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        _cleanup(game_id)

    def test_boulder_push_endpoint(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Strength")
        _grant_badges(game_id, ["rainbow"])
        use_strength(game_id, "route_2", 14, 10, 0)
        resp = client.post("/api/hm/boulder/push", json={
            "game_id": game_id, "obstacle_id": "route_2_boulder_1", "direction": "right",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["new_x"] == 15
        _cleanup(game_id)

    def test_obstacles_list_endpoint(self):
        resp = client.get("/api/hm/obstacles/route_1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_obstacle_state_endpoint(self):
        game_id = _create_test_game()
        resp = client.get(f"/api/hm/obstacles/route_1/state/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        _cleanup(game_id)

    def test_surf_state_endpoint(self):
        game_id = _create_test_game()
        resp = client.get(f"/api/hm/surf/state/{game_id}")
        assert resp.status_code == 200
        assert resp.json()["surfing"] is False
        _cleanup(game_id)

    def test_exit_surf_endpoint(self):
        game_id = _create_test_game()
        _give_hm_move(game_id, 0, "Surf")
        _grant_badges(game_id, ["soul"])
        use_surf(game_id, "pallet_town", 11, 15, 0)
        resp = client.post("/api/hm/surf/exit", json={
            "game_id": game_id, "map_id": "pallet_town", "x": 11, "y": 15,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        _cleanup(game_id)

    def test_exit_surf_endpoint_invalid_game(self):
        resp = client.post("/api/hm/surf/exit", json={
            "game_id": "bad_id", "map_id": "pallet_town", "x": 0, "y": 0,
        })
        assert resp.status_code == 404
