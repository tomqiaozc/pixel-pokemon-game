"""Tests for Sprint 14: Lavender Town maps.

These tests verify Lavender Town, its buildings, Pokemon Tower floors,
and map connections.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

from backend.services.map_service import get_map
from backend.services.encounter_service import get_encounter_table


# ──── Lavender Town Map ──────────────────────────────────

class TestLavenderTownMap:
    def test_lavender_town_exists(self):
        """maps.json must contain lavender_town."""
        game_map = get_map("lavender_town")
        assert game_map is not None
        assert game_map.map_type == "city"

    def test_lavender_connections(self):
        """Lavender Town should connect west→route_8, south→route_12."""
        game_map = get_map("lavender_town")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("west") == "route_8"
        assert conn_dirs.get("south") == "route_12"

    def test_lavender_buildings_count(self):
        """Lavender Town should have 4 buildings."""
        game_map = get_map("lavender_town")
        assert len(game_map.buildings) == 4

    def test_pokemon_center_exists(self):
        """maps.json must contain lavender_pokemon_center."""
        game_map = get_map("lavender_pokemon_center")
        assert game_map is not None

    def test_pokemart_exists(self):
        """maps.json must contain lavender_pokemart."""
        game_map = get_map("lavender_pokemart")
        assert game_map is not None

    def test_volunteer_house_exists(self):
        """maps.json must contain lavender_volunteer_house."""
        game_map = get_map("lavender_volunteer_house")
        assert game_map is not None

    def test_pokemon_tower_1f_exists(self):
        """maps.json must contain pokemon_tower_1f."""
        game_map = get_map("pokemon_tower_1f")
        assert game_map is not None

    def test_pokemon_tower_top_exists(self):
        """maps.json must contain pokemon_tower_top."""
        game_map = get_map("pokemon_tower_top")
        assert game_map is not None
