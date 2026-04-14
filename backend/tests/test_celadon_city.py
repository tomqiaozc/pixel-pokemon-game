"""Tests for Sprint 15: Celadon City maps."""
import pytest
from backend.services.map_service import get_map


class TestCeladonCityMap:
    def test_celadon_city_exists(self):
        game_map = get_map("celadon_city")
        assert game_map is not None
        assert game_map.map_type == "city"

    def test_celadon_connections(self):
        game_map = get_map("celadon_city")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("east") == "route_7"
        assert conn_dirs.get("west") == "route_16"

    def test_celadon_buildings_count(self):
        game_map = get_map("celadon_city")
        assert len(game_map.buildings) == 6

    def test_department_store_exists(self):
        game_map = get_map("celadon_department_store_1f")
        assert game_map is not None

    def test_game_corner_exists(self):
        game_map = get_map("celadon_game_corner")
        assert game_map is not None

    def test_celadon_gym_exists(self):
        game_map = get_map("celadon_gym")
        assert game_map is not None
        assert game_map.map_type == "gym"

    def test_route_16_exists(self):
        game_map = get_map("route_16")
        assert game_map is not None
        assert game_map.map_type == "route"

    def test_cycling_road_exists(self):
        game_map = get_map("cycling_road")
        assert game_map is not None
