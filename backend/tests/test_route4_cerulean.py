"""Tests for Sprint 11 QA-A1: Route 4 & Cerulean City Maps.

These tests define expected behavior for Route 4, Cerulean City, map
connections, encounter tables, trainers, NPCs, and map transitions.
They are written ahead of backend implementation and will FAIL until
the backend data is committed.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.map_service import get_map, transition_map, enter_building
from backend.services.encounter_service import get_encounter_table, get_species
from backend.services.gym_service import get_trainers_on_map
from backend.services.npc_service import get_npcs_by_map
from backend.services.game_service import create_game

client = TestClient(app)


def _create_test_game() -> str:
    game = create_game("MapTester", 1)
    return game["id"]


# ──── Route 4 Map ────────────────────────────────────────────

class TestRoute4Map:
    def test_route_4_map_exists(self):
        game_map = get_map("route_4")
        assert game_map is not None
        assert game_map.display_name == "Route 4"
        assert game_map.map_type == "route"

    def test_route_4_dimensions(self):
        game_map = get_map("route_4")
        assert game_map.width == 30
        assert game_map.height == 20

    def test_route_4_connections(self):
        game_map = get_map("route_4")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("west") == "mt_moon_entrance"
        assert conn_dirs.get("east") == "cerulean_city"

    def test_route_4_encounter_zones(self):
        game_map = get_map("route_4")
        assert len(game_map.encounter_zones) >= 1
        table_ids = {z.encounter_table_id for z in game_map.encounter_zones}
        assert "route_4" in table_ids

    def test_route_4_trainers_count(self):
        game_map = get_map("route_4")
        assert len(game_map.trainers) == 3


# ──── Mt. Moon East Exit ─────────────────────────────────────

class TestMtMoonExit:
    def test_mt_moon_east_connection(self):
        """Mt. Moon entrance should have an east connection to Route 4."""
        game_map = get_map("mt_moon_entrance")
        assert game_map is not None
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("east") == "route_4"


# ──── Cerulean City Map ──────────────────────────────────────

class TestCeruleanCityMap:
    def test_cerulean_city_map_exists(self):
        game_map = get_map("cerulean_city")
        assert game_map is not None
        assert game_map.display_name == "Cerulean City"
        assert game_map.map_type == "town"

    def test_cerulean_buildings_count(self):
        game_map = get_map("cerulean_city")
        assert len(game_map.buildings) == 4

    def test_cerulean_building_names(self):
        game_map = get_map("cerulean_city")
        building_names = {b.name for b in game_map.buildings}
        assert "Pokemon Center" in building_names
        assert "Poke Mart" in building_names
        assert "Cerulean Gym" in building_names
        assert "Bike Shop" in building_names

    def test_cerulean_interior_maps_exist(self):
        """All 4 interior maps referenced by buildings should exist."""
        game_map = get_map("cerulean_city")
        for building in game_map.buildings:
            if building.interior_map_id:
                interior = get_map(building.interior_map_id)
                assert interior is not None, f"Interior map {building.interior_map_id} not found"

    def test_cerulean_npcs_count(self):
        game_map = get_map("cerulean_city")
        assert len(game_map.npcs) >= 5

    def test_cerulean_connection_to_route_4(self):
        game_map = get_map("cerulean_city")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("west") == "route_4"

    def test_cerulean_surfing_encounter_zone(self):
        game_map = get_map("cerulean_city")
        surf_zones = [z for z in game_map.encounter_zones
                      if "surfing" in z.encounter_table_id]
        assert len(surf_zones) >= 1


# ──── Interior Maps ──────────────────────────────────────────

class TestCeruleanInteriors:
    def test_cerulean_pokemon_center_exists(self):
        game_map = get_map("cerulean_pokemon_center")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_cerulean_pokemart_exists(self):
        game_map = get_map("cerulean_pokemart")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_cerulean_gym_map_exists(self):
        game_map = get_map("cerulean_gym")
        assert game_map is not None
        assert game_map.map_type == "gym"

    def test_bike_shop_exists(self):
        game_map = get_map("bike_shop")
        assert game_map is not None
        assert game_map.map_type == "interior"


# ──── Encounter Tables ───────────────────────────────────────

class TestEncounterTables:
    def test_route_4_encounter_table_exists(self):
        table = get_encounter_table("route_4")
        assert table is not None
        assert table.encounter_type == "grass"

    def test_route_4_encounter_species(self):
        table = get_encounter_table("route_4")
        species_ids = {e.species_id for e in table.encounters}
        # Should include Ekans, Sandshrew, Oddish, Nidoran-F, Nidoran-M, Abra, Jigglypuff
        assert 23 in species_ids  # Ekans
        assert 43 in species_ids  # Oddish
        assert 63 in species_ids  # Abra

    def test_route_4_encounter_levels(self):
        table = get_encounter_table("route_4")
        for entry in table.encounters:
            assert entry.min_level >= 8
            assert entry.max_level <= 14

    def test_cerulean_surfing_encounter_table(self):
        table = get_encounter_table("cerulean_city_surfing")
        assert table is not None
        assert table.encounter_type == "water"
        species_ids = {e.species_id for e in table.encounters}
        assert len(species_ids) >= 2


# ──── Map Transitions ────────────────────────────────────────

class TestMapTransitions:
    def test_transition_mt_moon_to_route4(self):
        game_id = _create_test_game()
        result = transition_map(game_id, "mt_moon_entrance", "east")
        assert result is not None
        assert result.target_map_id == "route_4"

    def test_transition_route4_to_cerulean(self):
        game_id = _create_test_game()
        result = transition_map(game_id, "route_4", "east")
        assert result is not None
        assert result.target_map_id == "cerulean_city"

    def test_transition_cerulean_to_route4(self):
        game_id = _create_test_game()
        result = transition_map(game_id, "cerulean_city", "west")
        assert result is not None
        assert result.target_map_id == "route_4"

    def test_building_enter_cerulean_gym(self):
        game_id = _create_test_game()
        # Move player to cerulean_city first
        from backend.services.game_service import get_game
        game = get_game(game_id)
        game["player"]["position"]["map_id"] = "cerulean_city"
        # Cerulean Gym door coords from plan: door_x=17, door_y=8
        result = enter_building(game_id, 17, 8)
        assert result is not None
        assert result.target_map_id == "cerulean_gym"


# ──── API Endpoint Integration ───────────────────────────────

class TestMapEndpoints:
    def test_route_4_map_endpoint(self):
        resp = client.get("/api/maps/route_4")
        assert resp.status_code == 200
        data = resp.json()
        map_data = data.get("map", data)
        assert map_data["display_name"] == "Route 4"

    def test_cerulean_city_map_endpoint(self):
        resp = client.get("/api/maps/cerulean_city")
        assert resp.status_code == 200
        data = resp.json()
        map_data = data.get("map", data)
        assert map_data["display_name"] == "Cerulean City"

    def test_transition_endpoint_mt_moon_to_route4(self):
        game_id = _create_test_game()
        resp = client.post("/api/maps/transition", json={
            "game_id": game_id,
            "from_map": "mt_moon_entrance",
            "direction": "east",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_map_id"] == "route_4"
