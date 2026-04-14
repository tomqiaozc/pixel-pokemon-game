"""Tests for Sprint 26: Rock Tunnel, Underground Path E-W, Daycare, fishing encounters.

These tests verify Rock Tunnel maps, Underground Path, Daycare interior,
fishing encounter tables, utility NPCs, and new dialogues.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── New Maps ──────────────────────────────────────────────

class TestNewMaps:
    EXPECTED_MAPS = [
        ("rock_tunnel_1f", "dungeon"),
        ("rock_tunnel_b1f", "dungeon"),
        ("underground_path_ew", "interior"),
        ("daycare_interior", "interior"),
    ]

    @pytest.mark.parametrize("map_id,map_type", EXPECTED_MAPS)
    def test_map_exists(self, map_id, map_type):
        maps = _load_json("maps.json")
        found = next((m for m in maps if m["id"] == map_id), None)
        assert found is not None, f"Map {map_id} not found"
        assert found["map_type"] == map_type

    def test_rock_tunnel_has_encounters(self):
        maps = _load_json("maps.json")
        rt1f = next(m for m in maps if m["id"] == "rock_tunnel_1f")
        assert len(rt1f.get("encounter_zones", [])) >= 1
        rtb1f = next(m for m in maps if m["id"] == "rock_tunnel_b1f")
        assert len(rtb1f.get("encounter_zones", [])) >= 1

    def test_rock_tunnel_has_trainers(self):
        maps = _load_json("maps.json")
        rt1f = next(m for m in maps if m["id"] == "rock_tunnel_1f")
        assert len(rt1f.get("trainers", [])) >= 2
        rtb1f = next(m for m in maps if m["id"] == "rock_tunnel_b1f")
        assert len(rtb1f.get("trainers", [])) >= 2

    def test_underground_path_no_encounters(self):
        maps = _load_json("maps.json")
        ug = next(m for m in maps if m["id"] == "underground_path_ew")
        assert len(ug.get("encounter_zones", [])) == 0

    def test_daycare_has_npc(self):
        maps = _load_json("maps.json")
        dc = next(m for m in maps if m["id"] == "daycare_interior")
        assert len(dc.get("npcs", [])) >= 1

    def test_total_maps_count(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132


# ──── Encounter Tables ──────────────────────────────────────

class TestNewEncounterTables:
    EXPECTED_TABLES = [
        "rock_tunnel",
        "route_19_fishing",
        "route_20_fishing",
        "route_21_fishing",
    ]

    @pytest.mark.parametrize("table_id", EXPECTED_TABLES)
    def test_table_exists(self, table_id):
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

    def test_rock_tunnel_is_cave(self):
        tables = _load_json("encounter_tables.json")
        assert tables["rock_tunnel"]["encounter_type"] == "cave"

    def test_fishing_tables_are_fishing(self):
        tables = _load_json("encounter_tables.json")
        for tid in ["route_19_fishing", "route_20_fishing", "route_21_fishing"]:
            assert tables[tid]["encounter_type"] == "fishing"

    def test_total_encounter_tables(self):
        tables = _load_json("encounter_tables.json")
        assert len(tables) == 50


# ──── Trainers ──────────────────────────────────────────────

class TestRockTunnelTrainers:
    EXPECTED_TRAINERS = [
        "rock_tunnel_hiker_1",
        "rock_tunnel_pokemaniac_1",
        "rock_tunnel_jr_trainer_1",
        "rock_tunnel_hiker_2",
    ]

    @pytest.mark.parametrize("trainer_id", EXPECTED_TRAINERS)
    def test_trainer_exists(self, trainer_id):
        trainers = _load_json("trainers.json")
        found = next((t for t in trainers if t["id"] == trainer_id), None)
        assert found is not None, f"Trainer {trainer_id} not found"
        assert len(found.get("pokemon_team", [])) >= 1

    def test_total_trainer_count(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 116


# ──── NPCs ──────────────────────────────────────────────────

class TestUtilityNPCs:
    EXPECTED_NPCS = [
        ("daycare_man", "service"),
        ("move_deleter", "service"),
    ]

    @pytest.mark.parametrize("npc_id,npc_type", EXPECTED_NPCS)
    def test_npc_exists(self, npc_id, npc_type):
        npcs = _load_json("npcs.json")
        found = next((n for n in npcs if n["id"] == npc_id), None)
        assert found is not None, f"NPC {npc_id} not found"
        assert found["npc_type"] == npc_type

    def test_total_npc_count(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 94


# ──── Dialogues ─────────────────────────────────────────────

class TestNewDialogues:
    EXPECTED_DIALOGUES = [
        "daycare_man_dialogue",
        "name_rater_dialogue",
        "move_deleter_dialogue",
    ]

    @pytest.mark.parametrize("dialogue_id", EXPECTED_DIALOGUES)
    def test_dialogue_exists(self, dialogue_id):
        dialogues = _load_json("dialogues.json")
        assert dialogue_id in dialogues
        assert len(dialogues[dialogue_id].get("nodes", [])) >= 2

    def test_total_dialogue_count(self):
        dialogues = _load_json("dialogues.json")
        assert len(dialogues) == 72


# ──── Counts Unchanged ──────────────────────────────────────

class TestCountsUnchanged:
    def test_still_eight_gyms(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8

    def test_species_count_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151

    def test_items_count_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 48
