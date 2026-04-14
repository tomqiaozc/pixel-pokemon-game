"""Tests for Sprint 13 QA: Vermilion City maps and data.

These tests verify Vermilion City, its buildings, S.S. Anne interiors,
Route 6/11 connections, and encounter tables.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

import json
import os
import pytest

from backend.services.map_service import get_map
from backend.services.encounter_service import get_encounter_table

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Vermilion City Map ───────────────────────────────────

class TestVermilionCityMap:
    def test_vermilion_city_map_exists(self):
        """maps.json must contain vermilion_city."""
        game_map = get_map("vermilion_city")
        assert game_map is not None
        assert game_map.map_type == "city"

    def test_vermilion_city_connections(self):
        """Vermilion City should connect north→route_6, east→route_11."""
        game_map = get_map("vermilion_city")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("north") == "route_6"
        assert conn_dirs.get("east") == "route_11"

    def test_vermilion_buildings_count(self):
        """Vermilion City should have 7 buildings."""
        game_map = get_map("vermilion_city")
        assert len(game_map.buildings) == 7


# ──── Vermilion Buildings ──────────────────────────────────

class TestVermilionBuildings:
    def test_vermilion_pokemon_center_exists(self):
        """maps.json must contain vermilion_pokemon_center."""
        game_map = get_map("vermilion_pokemon_center")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_vermilion_pokemart_exists(self):
        """maps.json must contain vermilion_pokemart."""
        game_map = get_map("vermilion_pokemart")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_vermilion_fan_club_exists(self):
        """maps.json must contain vermilion_fan_club."""
        game_map = get_map("vermilion_fan_club")
        assert game_map is not None
        assert game_map.map_type == "interior"

    def test_vermilion_gym_exists_in_maps(self):
        """maps.json must contain vermilion_gym interior."""
        game_map = get_map("vermilion_gym")
        assert game_map is not None
        assert game_map.map_type == "gym"

    def test_digletts_cave_entrance_exists(self):
        """maps.json must contain digletts_cave_entrance."""
        game_map = get_map("digletts_cave_entrance")
        assert game_map is not None


# ──── S.S. Anne Interiors ──────────────────────────────────

class TestSSAnneInteriors:
    def test_ss_anne_deck_exists(self):
        """maps.json must contain ss_anne_deck."""
        game_map = get_map("ss_anne_deck")
        assert game_map is not None

    def test_ss_anne_cabins_exists(self):
        """maps.json must contain ss_anne_cabins."""
        game_map = get_map("ss_anne_cabins")
        assert game_map is not None

    def test_ss_anne_kitchen_exists(self):
        """maps.json must contain ss_anne_kitchen."""
        game_map = get_map("ss_anne_kitchen")
        assert game_map is not None

    def test_ss_anne_captains_room_exists(self):
        """maps.json must contain ss_anne_captains_room."""
        game_map = get_map("ss_anne_captains_room")
        assert game_map is not None


# ──── Route Connections ────────────────────────────────────

class TestRouteConnections:
    def test_route_6_south_connection(self):
        """Route 6 should connect south to vermilion_city."""
        game_map = get_map("route_6")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("south") == "vermilion_city"

    def test_route_11_map_exists(self):
        """maps.json must contain route_11."""
        game_map = get_map("route_11")
        assert game_map is not None
        assert game_map.map_type == "route"


# ──── Encounter Tables ─────────────────────────────────────

class TestEncounterTables:
    def test_route_11_encounter_table(self):
        """encounter_tables.json must have route_11 encounters."""
        table = get_encounter_table("route_11")
        assert table is not None
        assert table.encounter_type == "grass"
        assert len(table.encounters) >= 1
