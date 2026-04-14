"""Tests for Sprint 22: Legendary Birds (Articuno, Zapdos, Moltres).

These tests verify the legendary bird species, dungeon maps, encounter tables,
and quest definitions.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Legendary Bird Maps ──────────────────────────────────

class TestLegendaryBirdMaps:
    """All 5 new maps must exist in maps.json."""

    EXPECTED_MAPS = [
        "seafoam_islands_1f",
        "seafoam_islands_b1f",
        "seafoam_islands_b2f",
        "power_plant",
        "moltres_chamber",
    ]

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_exists(self, map_id):
        maps = _load_json("maps.json")
        found = next((m for m in maps if m["id"] == map_id), None)
        assert found is not None, f"Map {map_id} not found in maps.json"

    def test_total_maps_count(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132


# ──── Legendary Bird Species ──────────────────────────────

class TestLegendaryBirdSpecies:
    EXPECTED_SPECIES = [
        (144, "Articuno"),
        (145, "Zapdos"),
        (146, "Moltres"),
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
            assert species is not None, f"Species {name} (ID {sid}) not found"
            stats = species.get("stats", {})
            for stat in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
                assert stat in stats, f"Species {name} (ID {sid}) missing stat {stat}"

    def test_legendary_catch_rate(self):
        species_data = _load_json("pokemon_species.json")
        for sid, name in self.EXPECTED_SPECIES:
            species = next(s for s in species_data if s["id"] == sid)
            assert species["catch_rate"] == 3, f"{name} should have catch rate 3"

    def test_total_species_count(self):
        species_data = _load_json("pokemon_species.json")
        assert len(species_data) == 151


# ──── Encounter Tables ──────────────────────────────────────

class TestLegendaryEncounters:
    def test_seafoam_islands_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "seafoam_islands" in tables, "Encounter table seafoam_islands not found"
        assert len(tables["seafoam_islands"].get("encounters", [])) >= 1

    def test_power_plant_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "power_plant" in tables, "Encounter table power_plant not found"
        assert len(tables["power_plant"].get("encounters", [])) >= 1

    def test_total_encounter_tables(self):
        tables = _load_json("encounter_tables.json")
        assert len(tables) == 52


# ──── Quest Definitions ──────────────────────────────────────

class TestLegendaryQuests:
    def test_articuno_quest_defined(self):
        from backend.services.quest_service import _QUEST_DEFS
        quest = next((q for q in _QUEST_DEFS if q["id"] == "legendary_articuno"), None)
        assert quest is not None
        assert quest["type"] == "side"
        assert len(quest["objectives"]) == 2

    def test_zapdos_quest_defined(self):
        from backend.services.quest_service import _QUEST_DEFS
        quest = next((q for q in _QUEST_DEFS if q["id"] == "legendary_zapdos"), None)
        assert quest is not None
        assert quest["type"] == "side"

    def test_moltres_quest_defined(self):
        from backend.services.quest_service import _QUEST_DEFS
        quest = next((q for q in _QUEST_DEFS if q["id"] == "legendary_moltres"), None)
        assert quest is not None
        assert quest["type"] == "side"


# ──── Counts Unchanged ──────────────────────────────────────

class TestCountsUnchanged:
    def test_still_eight_gyms(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8

    def test_trainer_count_unchanged(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 116

    def test_npc_count_unchanged(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 94
