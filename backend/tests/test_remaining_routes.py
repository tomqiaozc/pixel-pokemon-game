"""Tests for Sprint 25: Remaining Kanto Routes (9, 10, 13-15, 17-19).

These tests verify the 8 new route maps, encounter tables, and trainers.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Route Maps ──────────────────────────────────────────

class TestRouteMaps:
    EXPECTED_MAPS = [
        "route_9",
        "route_10",
        "route_13",
        "route_14",
        "route_15",
        "route_17",
        "route_18",
        "route_19",
    ]

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_exists(self, map_id):
        maps = _load_json("maps.json")
        found = next((m for m in maps if m["id"] == map_id), None)
        assert found is not None, f"Map {map_id} not found in maps.json"
        assert found["map_type"] == "route"

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_has_connections(self, map_id):
        maps = _load_json("maps.json")
        found = next(m for m in maps if m["id"] == map_id)
        assert len(found.get("connections", [])) >= 2, (
            f"Map {map_id} should have at least 2 connections"
        )

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_has_encounter_zones(self, map_id):
        maps = _load_json("maps.json")
        found = next(m for m in maps if m["id"] == map_id)
        zones = found.get("encounter_zones", [])
        assert len(zones) >= 1, f"Map {map_id} should have encounter zones"
        for zone in zones:
            assert "x" in zone
            assert "y" in zone
            assert "width" in zone
            assert "height" in zone
            assert "encounter_table_id" in zone

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_has_trainers(self, map_id):
        maps = _load_json("maps.json")
        found = next(m for m in maps if m["id"] == map_id)
        trainers = found.get("trainers", [])
        assert len(trainers) >= 2, f"Map {map_id} should have at least 2 trainers"

    def test_total_maps_count(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132


# ──── Encounter Tables ──────────────────────────────────────

class TestRouteEncounterTables:
    EXPECTED_TABLES = [
        "route_9",
        "route_10",
        "route_13",
        "route_14",
        "route_15",
        "route_17",
        "route_18",
        "route_19",
    ]

    @pytest.mark.parametrize("table_id", EXPECTED_TABLES)
    def test_encounter_table_exists(self, table_id):
        tables = _load_json("encounter_tables.json")
        assert table_id in tables, f"Encounter table {table_id} not found"
        table = tables[table_id]
        assert "name" in table
        assert "encounter_type" in table
        assert "base_encounter_rate" in table
        assert len(table.get("encounters", [])) >= 2

    @pytest.mark.parametrize("table_id", EXPECTED_TABLES)
    def test_encounter_entries_valid(self, table_id):
        tables = _load_json("encounter_tables.json")
        for entry in tables[table_id]["encounters"]:
            assert "species_id" in entry
            assert "min_level" in entry
            assert "max_level" in entry
            assert "weight" in entry
            assert entry["min_level"] <= entry["max_level"]

    def test_total_encounter_tables(self):
        tables = _load_json("encounter_tables.json")
        assert len(tables) == 50


# ──── Trainers ──────────────────────────────────────────────

class TestRouteTrainers:
    EXPECTED_TRAINERS = [
        "route9_hiker_1",
        "route9_jr_trainer_1",
        "route9_bug_catcher_1",
        "route10_pokemaniac_1",
        "route10_hiker_1",
        "route13_bird_keeper_1",
        "route13_beauty_1",
        "route14_bird_keeper_1",
        "route14_biker_1",
        "route15_jr_trainer_1",
        "route15_beauty_1",
        "route17_cue_ball_1",
        "route17_biker_1",
        "route17_biker_2",
        "route18_bird_keeper_1",
        "route18_bird_keeper_2",
        "route19_swimmer_1",
        "route19_swimmer_2",
    ]

    @pytest.mark.parametrize("trainer_id", EXPECTED_TRAINERS)
    def test_trainer_exists(self, trainer_id):
        trainers = _load_json("trainers.json")
        found = next((t for t in trainers if t["id"] == trainer_id), None)
        assert found is not None, f"Trainer {trainer_id} not found"

    @pytest.mark.parametrize("trainer_id", EXPECTED_TRAINERS)
    def test_trainer_has_team(self, trainer_id):
        trainers = _load_json("trainers.json")
        found = next(t for t in trainers if t["id"] == trainer_id)
        assert len(found.get("pokemon_team", [])) >= 1

    def test_total_trainer_count(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 116


# ──── Counts Unchanged ──────────────────────────────────────

class TestCountsUnchanged:
    def test_still_eight_gyms(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8

    def test_npc_count_unchanged(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 94

    def test_species_count_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151

    def test_dialogue_count_unchanged(self):
        dialogues = _load_json("dialogues.json")
        assert len(dialogues) == 72
