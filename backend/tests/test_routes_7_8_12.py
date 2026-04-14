"""Tests for Sprint 14 QA: Routes 7, 8, and 12.

These tests verify Route 7, Route 8, and Route 12 maps,
encounter tables, and map connections.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

from backend.services.map_service import get_map
from backend.services.encounter_service import get_encounter_table


# ──── Map Existence ──────────────────────────────────────

class TestMapExistence:
    def test_route_7_map_exists(self):
        """maps.json must contain route_7."""
        game_map = get_map("route_7")
        assert game_map is not None
        assert game_map.map_type == "route"

    def test_route_8_map_exists(self):
        """maps.json must contain route_8."""
        game_map = get_map("route_8")
        assert game_map is not None
        assert game_map.map_type == "route"

    def test_route_12_map_exists(self):
        """maps.json must contain route_12."""
        game_map = get_map("route_12")
        assert game_map is not None
        assert game_map.map_type == "route"


# ──── Map Connections ────────────────────────────────────

class TestMapConnections:
    def test_route_8_east_connection(self):
        """Route 8 should connect east to lavender_town."""
        game_map = get_map("route_8")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("east") == "lavender_town"

    def test_route_12_north_connection(self):
        """Route 12 should connect north to lavender_town."""
        game_map = get_map("route_12")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("north") == "lavender_town"


# ──── Encounter Tables ───────────────────────────────────

class TestEncounterTables:
    def test_route_8_encounter_table(self):
        """encounter_tables.json must have route_8 encounters."""
        table = get_encounter_table("route_8")
        assert table is not None
        assert table.encounter_type == "grass"
        assert len(table.encounters) >= 1

    def test_route_12_encounter_table(self):
        """encounter_tables.json must have route_12 encounters."""
        table = get_encounter_table("route_12")
        assert table is not None
        assert table.encounter_type == "grass"
        assert len(table.encounters) >= 1
