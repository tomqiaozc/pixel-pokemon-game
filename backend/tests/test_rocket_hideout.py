"""Tests for Sprint 16: Rocket Hideout maps and event service."""
from __future__ import annotations

from backend.services.map_service import get_map


class TestRocketHideoutMaps:
    def test_rocket_hideout_b1f_exists(self):
        game_map = get_map("rocket_hideout_b1f")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_rocket_hideout_b2f_exists(self):
        game_map = get_map("rocket_hideout_b2f")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_rocket_hideout_b3f_exists(self):
        game_map = get_map("rocket_hideout_b3f")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_rocket_hideout_b4f_exists(self):
        game_map = get_map("rocket_hideout_b4f")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_saffron_gate_north_exists(self):
        game_map = get_map("saffron_gate_north")
        assert game_map is not None

    def test_saffron_gate_south_exists(self):
        game_map = get_map("saffron_gate_south")
        assert game_map is not None


class TestRocketHideoutService:
    def test_initial_state(self):
        from backend.services.rocket_hideout_service import get_state
        result = get_state("test_rh_1")
        assert result["state"] == "not_entered"

    def test_enter_hideout(self):
        from backend.services.rocket_hideout_service import enter_hideout, get_state
        enter_hideout("test_rh_2")
        result = get_state("test_rh_2")
        assert result["state"] == "b1f_entered"

    def test_clear_b2f(self):
        from backend.services.rocket_hideout_service import enter_hideout, clear_floor, get_state
        enter_hideout("test_rh_3")
        clear_floor("test_rh_3", "b2f")
        result = get_state("test_rh_3")
        assert result["state"] == "b2f_cleared"

    def test_clear_b3f(self):
        from backend.services.rocket_hideout_service import enter_hideout, clear_floor, get_state
        enter_hideout("test_rh_4")
        clear_floor("test_rh_4", "b2f")
        clear_floor("test_rh_4", "b3f")
        result = get_state("test_rh_4")
        assert result["state"] == "b3f_cleared"

    def test_defeat_giovanni(self):
        from backend.services.rocket_hideout_service import enter_hideout, clear_floor, defeat_giovanni, get_state
        enter_hideout("test_rh_5")
        clear_floor("test_rh_5", "b2f")
        clear_floor("test_rh_5", "b3f")
        defeat_giovanni("test_rh_5")
        result = get_state("test_rh_5")
        assert result["state"] == "giovanni_defeated"

    def test_cannot_skip_floors(self):
        from backend.services.rocket_hideout_service import clear_floor
        result = clear_floor("test_rh_6", "b3f")
        assert "error" in result
