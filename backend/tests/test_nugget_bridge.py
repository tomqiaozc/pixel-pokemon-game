"""Tests for Sprint 12 QA-A2: Nugget Bridge (Route 24) & Route 25.

These tests verify Route 24/25 maps, Nugget Bridge trainers, encounter
tables, the Nugget Bridge gauntlet service, and map connections.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.map_service import get_map
from backend.services.encounter_service import get_encounter_table
from backend.services.gym_service import get_trainer
from backend.services.game_service import create_game

client = TestClient(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def _create_test_game() -> str:
    game = create_game("BridgeTester", 1)
    return game["id"]


# ──── Map Existence ─────────────────────────────────────────

class TestMapExistence:
    def test_route_24_map_exists(self):
        """maps.json must contain route_24."""
        game_map = get_map("route_24")
        assert game_map is not None
        assert game_map.display_name == "Route 24 - Nugget Bridge"
        assert game_map.map_type == "route"

    def test_route_25_map_exists(self):
        """maps.json must contain route_25."""
        game_map = get_map("route_25")
        assert game_map is not None
        assert game_map.display_name == "Route 25"
        assert game_map.map_type == "route"

    def test_bills_house_map_exists(self):
        """maps.json must contain bills_house interior."""
        game_map = get_map("bills_house")
        assert game_map is not None
        assert game_map.display_name == "Bill's House"
        assert game_map.map_type == "interior"


# ──── Route 24 Trainers ────────────────────────────────────

class TestRoute24Trainers:
    def test_route_24_has_trainers(self):
        """Route 24 should have 6 trainers (5 bridge + Rocket Grunt)."""
        game_map = get_map("route_24")
        assert len(game_map.trainers) == 6

    def test_nugget_trainers_exist(self):
        """trainers.json must have nugget_trainer_1 through 5."""
        for i in range(1, 6):
            trainer = get_trainer(f"nugget_trainer_{i}")
            assert trainer is not None, f"nugget_trainer_{i} not found"
            assert len(trainer.pokemon_team) >= 1

    def test_rocket_grunt_nugget_exists(self):
        """trainers.json must have rocket_grunt_nugget."""
        trainer = get_trainer("rocket_grunt_nugget")
        assert trainer is not None, "rocket_grunt_nugget not found"
        assert len(trainer.pokemon_team) >= 1


# ──── Encounter Tables ──────────────────────────────────────

class TestEncounterTables:
    def test_route_24_encounter_table(self):
        """encounter_tables.json must have route_24 encounters."""
        table = get_encounter_table("route_24")
        assert table is not None
        assert table.encounter_type == "grass"
        assert len(table.encounters) >= 1

    def test_route_25_encounter_table(self):
        """encounter_tables.json must have route_25 encounters."""
        table = get_encounter_table("route_25")
        assert table is not None
        assert table.encounter_type == "grass"
        assert len(table.encounters) >= 1


# ──── Nugget Bridge Gauntlet Service ────────────────────────

class TestNuggetBridgeGauntlet:
    def test_nugget_bridge_initial_state(self):
        """GET /api/nugget-bridge/state/{game_id} should return initial state."""
        game_id = _create_test_game()
        resp = client.get(f"/api/nugget-bridge/state/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        # Initial state: no trainers defeated
        assert data.get("trainers_defeated", 0) == 0

    def test_defeat_trainer(self):
        """POST /api/nugget-bridge/defeat should record a trainer defeat."""
        game_id = _create_test_game()
        resp = client.post("/api/nugget-bridge/defeat", json={
            "game_id": game_id,
            "trainer_index": 0,
        })
        assert resp.status_code == 200

    def test_defeat_all_5(self):
        """After defeating 5 trainers, bridge should be clear."""
        game_id = _create_test_game()
        for i in range(5):
            resp = client.post("/api/nugget-bridge/defeat", json={
                "game_id": game_id,
                "trainer_index": i,
            })
            assert resp.status_code == 200
        # Check state
        resp = client.get(f"/api/nugget-bridge/state/{game_id}")
        data = resp.json()
        assert data.get("bridge_clear", False) is True

    def test_award_nugget_after_clear(self):
        """POST /api/nugget-bridge/award should succeed after clearing all 5."""
        game_id = _create_test_game()
        for i in range(5):
            client.post("/api/nugget-bridge/defeat", json={
                "game_id": game_id,
                "trainer_index": i,
            })
        resp = client.post("/api/nugget-bridge/award", json={
            "game_id": game_id,
        })
        assert resp.status_code == 200

    def test_award_nugget_before_clear(self):
        """Cannot award Nugget before clearing all 5 trainers."""
        game_id = _create_test_game()
        resp = client.post("/api/nugget-bridge/award", json={
            "game_id": game_id,
        })
        assert resp.status_code >= 400


# ──── Map Connections ───────────────────────────────────────

class TestMapConnections:
    def test_cerulean_north_connection(self):
        """Cerulean City should connect north to route_24."""
        game_map = get_map("cerulean_city")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("north") == "route_24"

    def test_route_24_south_connection(self):
        """Route 24 should connect south to cerulean_city."""
        game_map = get_map("route_24")
        conn_dirs = {c.direction: c.target_map_id for c in game_map.connections}
        assert conn_dirs.get("south") == "cerulean_city"
