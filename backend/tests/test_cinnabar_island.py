"""Tests for Sprint 19: Cinnabar Island, Blaine's Gym, Pokemon Mansion.

These tests verify Cinnabar Island maps, Blaine's Gym data, Pokemon Mansion
encounter tables, new species, items, trainers, and NPCs.
Written ahead of backend implementation -- will FAIL until data is committed.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Cinnabar Island Maps ──────────────────────────────────

class TestCinnabarIslandMaps:
    """All 10 new maps must exist in maps.json."""

    EXPECTED_MAPS = [
        "cinnabar_island",
        "cinnabar_pokemon_center",
        "cinnabar_pokemart",
        "cinnabar_gym",
        "pokemon_mansion_1f",
        "pokemon_mansion_2f",
        "pokemon_mansion_top",
        "pokemon_lab",
        "route_20",
        "route_21",
    ]

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_exists(self, map_id):
        maps = _load_json("maps.json")
        found = next((m for m in maps if m["id"] == map_id), None)
        assert found is not None, f"Map {map_id} not found in maps.json"

    def test_total_maps_count(self):
        maps = _load_json("maps.json")
        assert len(maps) == 112


# ──── Cinnabar Gym (Blaine) ─────────────────────────────────

class TestCinnabarGymData:
    def test_cinnabar_gym_exists_in_gyms(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "cinnabar_gym"), None)
        assert gym is not None

    def test_cinnabar_gym_leader_is_blaine(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "cinnabar_gym")
        assert gym["leader"]["name"] == "Blaine"

    def test_cinnabar_gym_type_is_fire(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "cinnabar_gym")
        assert gym["type_specialty"] == "fire"

    def test_cinnabar_gym_has_volcano_badge(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "cinnabar_gym")
        assert gym["badge_name"] == "Volcano Badge"

    def test_blaine_has_four_pokemon(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "cinnabar_gym")
        assert len(gym["leader"]["pokemon_team"]) == 4

    def test_total_gym_count(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8


# ──── New Pokemon Species ────────────────────────────────────

class TestCinnabarIslandSpecies:
    EXPECTED_SPECIES = [
        (58, "Growlithe"),
        (59, "Arcanine"),
        (77, "Ponyta"),
        (78, "Rapidash"),
        (126, "Magmar"),
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

    def test_total_species_count(self):
        species_data = _load_json("pokemon_species.json")
        assert len(species_data) == 105


# ──── New Items ──────────────────────────────────────────────

class TestCinnabarIslandItems:
    EXPECTED_ITEMS = [
        (64, "Secret Key"),
        (65, "TM38 Fire Blast"),
    ]

    @pytest.mark.parametrize("item_id,name", EXPECTED_ITEMS)
    def test_item_exists(self, item_id, name):
        items = _load_json("items.json")
        item = next((i for i in items if i.get("id") == item_id), None)
        assert item is not None, f"Item {name} (ID {item_id}) not found"
        assert item["name"] == name


# ──── Trainers ───────────────────────────────────────────────

class TestCinnabarIslandTrainers:
    def test_total_trainer_count(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 94

    def test_all_trainers_have_teams(self):
        trainers = _load_json("trainers.json")
        for trainer in trainers:
            assert len(trainer.get("pokemon_team", [])) >= 1, (
                f"Trainer {trainer.get('id')} has no pokemon team"
            )


# ──── NPCs ───────────────────────────────────────────────────

class TestCinnabarIslandNPCs:
    def test_total_npc_count(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 91


# ──── Encounter Tables ───────────────────────────────────────

class TestCinnabarEncounters:
    def test_route_20_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "route_20" in tables, "Encounter table route_20 not found"
        assert len(tables["route_20"].get("encounters", [])) >= 1

    def test_route_21_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "route_21" in tables, "Encounter table route_21 not found"
        assert len(tables["route_21"].get("encounters", [])) >= 1

    def test_pokemon_mansion_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "pokemon_mansion" in tables, "Encounter table pokemon_mansion not found"
        assert len(tables["pokemon_mansion"].get("encounters", [])) >= 1
