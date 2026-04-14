"""Tests for Sprint 18: Fuchsia City, Koga's Gym, Safari Zone.

These tests verify Fuchsia City maps, Koga's Gym data, Safari Zone
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


# ──── Fuchsia City Maps ───────────────────────────────────

class TestFuchsiaCityMaps:
    """All 8 new maps must exist in maps.json."""

    EXPECTED_MAPS = [
        "fuchsia_city",
        "fuchsia_pokemon_center",
        "fuchsia_pokemart",
        "fuchsia_gym",
        "safari_zone_entrance",
        "safari_zone_area_1",
        "safari_zone_area_2",
        "wardens_house",
    ]

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_exists(self, map_id):
        maps = _load_json("maps.json")
        found = next((m for m in maps if m["id"] == map_id), None)
        assert found is not None, f"Map {map_id} not found in maps.json"

    def test_total_maps_count(self):
        maps = _load_json("maps.json")
        assert len(maps) == 120


# ──── Fuchsia Gym (Koga) ─────────────────────────────────

class TestFuchsiaGymData:
    def test_fuchsia_gym_exists_in_gyms(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "fuchsia_gym"), None)
        assert gym is not None

    def test_fuchsia_gym_leader_is_koga(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "fuchsia_gym")
        assert gym["leader"]["name"] == "Koga"

    def test_fuchsia_gym_type_is_poison(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "fuchsia_gym")
        assert gym["type_specialty"] == "poison"

    def test_fuchsia_gym_has_soul_badge(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "fuchsia_gym")
        assert gym["badge_name"] == "Soul Badge"

    def test_koga_has_four_pokemon(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "fuchsia_gym")
        assert len(gym["leader"]["pokemon_team"]) == 4

    def test_total_gym_count(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8


# ──── New Pokemon Species ─────────────────────────────────

class TestFuchsiaCitySpecies:
    EXPECTED_SPECIES = [
        (48, "Venonat"),
        (49, "Venomoth"),
        (113, "Chansey"),
        (123, "Scyther"),
        (128, "Tauros"),
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


# ──── New Items ───────────────────────────────────────────

class TestFuchsiaCityItems:
    EXPECTED_ITEMS = [
        (61, "HM03 Surf"),
        (62, "HM04 Strength"),
        (63, "Gold Teeth"),
    ]

    @pytest.mark.parametrize("item_id,name", EXPECTED_ITEMS)
    def test_item_exists(self, item_id, name):
        items = _load_json("items.json")
        item = next((i for i in items if i.get("id") == item_id), None)
        assert item is not None, f"Item {name} (ID {item_id}) not found"
        assert item["name"] == name


# ──── Trainers ────────────────────────────────────────────

class TestFuchsiaCityTrainers:
    def test_three_new_trainers(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 94

    def test_all_trainers_have_teams(self):
        trainers = _load_json("trainers.json")
        for trainer in trainers:
            assert len(trainer.get("pokemon_team", [])) >= 1, (
                f"Trainer {trainer.get('id')} has no pokemon team"
            )


# ──── NPCs ────────────────────────────────────────────────

class TestFuchsiaCityNPCs:
    def test_total_npc_count(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 92


# ──── Encounter Tables ────────────────────────────────────

class TestSafariZoneEncounters:
    def test_safari_zone_1_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "safari_zone_1" in tables, "Encounter table safari_zone_1 not found"
        assert len(tables["safari_zone_1"].get("encounters", [])) >= 1

    def test_safari_zone_2_encounters_exist(self):
        tables = _load_json("encounter_tables.json")
        assert "safari_zone_2" in tables, "Encounter table safari_zone_2 not found"
        assert len(tables["safari_zone_2"].get("encounters", [])) >= 1
