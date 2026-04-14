"""Tests for Sprint 20: Viridian City Gym (Giovanni), Victory Road.

These tests verify Viridian Gym maps, Giovanni's Gym data, Victory Road
encounter tables, new items, trainers, and NPCs.
Written ahead of backend implementation -- will FAIL until data is committed.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Viridian City / Victory Road Maps ───────────────────────

class TestViridianGymMaps:
    """All 7 new maps must exist in maps.json."""

    EXPECTED_MAPS = [
        "viridian_gym",
        "route_22",
        "route_23",
        "victory_road_1f",
        "victory_road_2f",
        "indigo_plateau",
        "indigo_pokemon_center",
    ]

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_exists(self, map_id):
        maps = _load_json("maps.json")
        found = next((m for m in maps if m["id"] == map_id), None)
        assert found is not None, f"Map {map_id} not found in maps.json"

    def test_total_maps_count(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132


# ──── Viridian Gym (Giovanni) ─────────────────────────────────

class TestViridianGymData:
    def test_viridian_gym_exists_in_gyms(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "viridian_gym"), None)
        assert gym is not None

    def test_viridian_gym_leader_is_giovanni(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "viridian_gym")
        assert gym["leader"]["name"] == "Giovanni"

    def test_viridian_gym_type_is_ground(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "viridian_gym")
        assert gym["type_specialty"] == "ground"

    def test_viridian_gym_has_earth_badge(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "viridian_gym")
        assert gym["badge_name"] == "Earth Badge"

    def test_giovanni_has_five_pokemon(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "viridian_gym")
        assert len(gym["leader"]["pokemon_team"]) == 5

    def test_total_gym_count(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8


# ──── Giovanni's Pokemon Species ────────────────────────────────

class TestGiovanniSpecies:
    EXPECTED_SPECIES = [
        (51, "Dugtrio"),
        (95, "Onix"),
        (105, "Marowak"),
        (111, "Rhyhorn"),
        (112, "Rhydon"),
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
        assert len(species_data) == 151


# ──── New Items ──────────────────────────────────────────────

class TestViridianGymItems:
    EXPECTED_ITEMS = [
        (66, "TM26 Earthquake"),
    ]

    @pytest.mark.parametrize("item_id,name", EXPECTED_ITEMS)
    def test_item_exists(self, item_id, name):
        items = _load_json("items.json")
        item = next((i for i in items if i.get("id") == item_id), None)
        assert item is not None, f"Item {name} (ID {item_id}) not found"
        assert item["name"] == name


# ──── Trainers ───────────────────────────────────────────────

class TestViridianGymTrainers:
    def test_total_trainer_count(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 116

    def test_all_trainers_have_teams(self):
        trainers = _load_json("trainers.json")
        for trainer in trainers:
            assert len(trainer.get("pokemon_team", [])) >= 1, (
                f"Trainer {trainer.get('id')} has no pokemon team"
            )


# ──── NPCs ───────────────────────────────────────────────────

class TestViridianGymNPCs:
    def test_total_npc_count(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 94


# ──── Encounter Tables ───────────────────────────────────────

class TestViridianEncounters:
    def test_route_22_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "route_22" in tables, "Encounter table route_22 not found"
        assert len(tables["route_22"].get("encounters", [])) >= 1

    def test_victory_road_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "victory_road" in tables, "Encounter table victory_road not found"
        assert len(tables["victory_road"].get("encounters", [])) >= 1
