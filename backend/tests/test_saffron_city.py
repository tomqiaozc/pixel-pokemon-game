"""Tests for Sprint 17: Saffron City maps."""
from __future__ import annotations
from backend.services.map_service import get_map


class TestSaffronCityMaps:
    def test_saffron_city_exists(self):
        game_map = get_map("saffron_city")
        assert game_map is not None
        assert game_map.map_type == "city"

    def test_saffron_connections(self):
        game_map = get_map("saffron_city")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("west") == "route_7"
        assert conn_dirs.get("east") == "route_8"

    def test_saffron_buildings_count(self):
        game_map = get_map("saffron_city")
        assert len(game_map.buildings) >= 4

    def test_saffron_gym_exists(self):
        game_map = get_map("saffron_gym")
        assert game_map is not None
        assert game_map.map_type == "gym"

    def test_silph_co_1f_exists(self):
        game_map = get_map("silph_co_1f")
        assert game_map is not None

    def test_silph_co_top_exists(self):
        game_map = get_map("silph_co_top")
        assert game_map is not None

    def test_fighting_dojo_exists(self):
        game_map = get_map("fighting_dojo")
        assert game_map is not None


class TestSilphCoService:
    def test_initial_state(self):
        from backend.services.silph_co_service import get_state
        result = get_state("test_silph_1")
        assert result["state"] == "not_entered"

    def test_enter_silph(self):
        from backend.services.silph_co_service import enter_silph, get_state
        enter_silph("test_silph_2")
        result = get_state("test_silph_2")
        assert result["state"] == "infiltrating"

    def test_clear_rockets(self):
        from backend.services.silph_co_service import enter_silph, clear_rockets, get_state
        enter_silph("test_silph_3")
        clear_rockets("test_silph_3")
        result = get_state("test_silph_3")
        assert result["state"] == "rockets_cleared"

    def test_defeat_giovanni(self):
        from backend.services.silph_co_service import enter_silph, clear_rockets, defeat_giovanni_silph, get_state
        enter_silph("test_silph_4")
        clear_rockets("test_silph_4")
        defeat_giovanni_silph("test_silph_4")
        result = get_state("test_silph_4")
        assert result["state"] == "president_rescued"

    def test_cannot_skip(self):
        from backend.services.silph_co_service import clear_rockets
        result = clear_rockets("test_silph_5")
        assert "error" in result
