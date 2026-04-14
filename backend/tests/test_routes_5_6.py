"""Tests for Sprint 12 QA-A4: Routes 5/6 & Underground Path.

These tests verify Route 5, Route 6, and Underground Path maps,
encounter tables, trainers, and map connections.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

import json
import os
import pytest

from backend.services.map_service import get_map
from backend.services.encounter_service import get_encounter_table
from backend.services.gym_service import get_trainer

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ──── Map Existence ─────────────────────────────────────────

class TestMapExistence:
    def test_route_5_map_exists(self):
        """maps.json must contain route_5."""
        game_map = get_map("route_5")
        assert game_map is not None
        assert game_map.display_name == "Route 5"
        assert game_map.map_type == "route"

    def test_route_6_map_exists(self):
        """maps.json must contain route_6."""
        game_map = get_map("route_6")
        assert game_map is not None
        assert game_map.display_name == "Route 6"
        assert game_map.map_type == "route"

    def test_underground_path_exists(self):
        """maps.json must contain underground_path_ns."""
        game_map = get_map("underground_path_ns")
        assert game_map is not None
        assert game_map.display_name == "Underground Path"
        assert game_map.map_type == "interior"


# ──── Map Connections ───────────────────────────────────────

class TestMapConnections:
    def test_cerulean_south_connection(self):
        """Cerulean City should connect south to route_5."""
        game_map = get_map("cerulean_city")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("south") == "route_5"


# ──── Encounter Tables ──────────────────────────────────────

class TestEncounterTables:
    def test_route_5_encounter_table(self):
        """encounter_tables.json must have route_5 encounters."""
        table = get_encounter_table("route_5")
        assert table is not None
        assert table.encounter_type == "grass"
        assert len(table.encounters) >= 1

    def test_route_6_encounter_table(self):
        """encounter_tables.json must have route_6 encounters."""
        table = get_encounter_table("route_6")
        assert table is not None
        assert table.encounter_type == "grass"
        assert len(table.encounters) >= 1


# ──── Route 6 Trainers ──────────────────────────────────────

class TestRoute6Trainers:
    def test_route_6_trainers_exist(self):
        """trainers.json must have route6 trainers."""
        bug_catcher = get_trainer("route6_bug_catcher_1")
        assert bug_catcher is not None, "route6_bug_catcher_1 not found"
        assert len(bug_catcher.pokemon_team) >= 1

        youngster = get_trainer("route6_youngster_1")
        assert youngster is not None, "route6_youngster_1 not found"
        assert len(youngster.pokemon_team) >= 1


# ──── Underground Path ──────────────────────────────────────

class TestUndergroundPath:
    def test_underground_no_encounters(self):
        """Underground path should have no encounter_zones."""
        game_map = get_map("underground_path_ns")
        assert len(game_map.encounter_zones) == 0
