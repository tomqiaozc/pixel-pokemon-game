"""Tests for Sprint 23: Cerulean Cave, Mewtwo, Mew.

These tests verify Cerulean Cave maps, Mewtwo/Mew species,
encounter tables, quest definitions, guard NPC, and dialogue.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Cerulean Cave Maps ──────────────────────────────────

class TestCeruleanCaveMaps:
    EXPECTED_MAPS = [
        "cerulean_cave_1f",
        "cerulean_cave_2f",
        "cerulean_cave_b1f",
    ]

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_exists(self, map_id):
        maps = _load_json("maps.json")
        found = next((m for m in maps if m["id"] == map_id), None)
        assert found is not None, f"Map {map_id} not found in maps.json"

    def test_total_maps_count(self):
        maps = _load_json("maps.json")
        assert len(maps) == 120


# ──── Mewtwo & Mew Species ──────────────────────────────

class TestMewtwoMewSpecies:
    EXPECTED_SPECIES = [
        (150, "Mewtwo"),
        (151, "Mew"),
    ]

    @pytest.mark.parametrize("species_id,name", EXPECTED_SPECIES)
    def test_species_exists(self, species_id, name):
        species_data = _load_json("pokemon_species.json")
        species = next((s for s in species_data if s.get("id") == species_id), None)
        assert species is not None, f"Species {name} (ID {species_id}) not found"
        assert species["name"] == name

    def test_all_species_have_stats(self):
        species_data = _load_json("pokemon_species.json")
        for sid, name in self.EXPECTED_SPECIES:
            species = next((s for s in species_data if s.get("id") == sid), None)
            assert species is not None
            stats = species.get("stats", {})
            for stat in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
                assert stat in stats, f"Species {name} (ID {sid}) missing stat {stat}"

    def test_mewtwo_catch_rate(self):
        species_data = _load_json("pokemon_species.json")
        mewtwo = next(s for s in species_data if s["id"] == 150)
        assert mewtwo["catch_rate"] == 3

    def test_mew_is_psychic(self):
        species_data = _load_json("pokemon_species.json")
        mew = next(s for s in species_data if s["id"] == 151)
        assert "psychic" in mew["types"]

    def test_total_species_count(self):
        species_data = _load_json("pokemon_species.json")
        assert len(species_data) == 151


# ──── Encounter Table ──────────────────────────────────────

class TestCeruleanCaveEncounters:
    def test_cerulean_cave_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "cerulean_cave" in tables
        assert len(tables["cerulean_cave"].get("encounters", [])) >= 1

    def test_total_encounter_tables(self):
        tables = _load_json("encounter_tables.json")
        assert len(tables) == 38


# ──── Guard NPC ──────────────────────────────────────────

class TestCeruleanCaveGuard:
    def test_guard_npc_exists(self):
        npcs = _load_json("npcs.json")
        guard = next((n for n in npcs if n["id"] == "cerulean_cave_guard"), None)
        assert guard is not None
        assert guard["npc_type"] == "guard"

    def test_guard_dialogue_exists(self):
        dialogues = _load_json("dialogues.json")
        assert "cerulean_cave_guard_dialogue" in dialogues

    def test_total_npc_count(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 92

    def test_total_dialogue_count(self):
        dialogues = _load_json("dialogues.json")
        assert len(dialogues) == 70


# ──── Quest Definitions ──────────────────────────────────

class TestCeruleanCaveQuests:
    def test_cerulean_cave_quest_defined(self):
        from backend.services.quest_service import _QUEST_DEFS
        quest = next((q for q in _QUEST_DEFS if q["id"] == "cerulean_cave"), None)
        assert quest is not None
        assert quest["type"] == "side"
        assert quest["prerequisite_quests"] == ["champion"]

    def test_mewtwo_quest_defined(self):
        from backend.services.quest_service import _QUEST_DEFS
        quest = next((q for q in _QUEST_DEFS if q["id"] == "legendary_mewtwo"), None)
        assert quest is not None
        assert quest["type"] == "side"
        assert quest["prerequisite_quests"] == ["cerulean_cave"]


# ──── Counts Unchanged ──────────────────────────────────

class TestCountsUnchanged:
    def test_still_eight_gyms(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8

    def test_trainer_count_unchanged(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 94
