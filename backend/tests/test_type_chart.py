"""Tests for Sprint 29: Type chart, expanded abilities, secret areas.

These tests verify the type effectiveness chart, ability database,
and secret areas data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Type Chart ────────────────────────────────────────────

class TestTypeChart:
    def test_type_chart_exists(self):
        chart = _load_json("type_chart.json")
        assert len(chart) == 18

    EXPECTED_TYPES = [
        "normal", "fire", "water", "electric", "grass", "ice",
        "fighting", "poison", "ground", "flying", "psychic",
        "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy"
    ]

    @pytest.mark.parametrize("type_name", EXPECTED_TYPES)
    def test_type_exists(self, type_name):
        chart = _load_json("type_chart.json")
        assert type_name in chart, f"Type {type_name} not in chart"

    def test_fire_super_effective_on_grass(self):
        chart = _load_json("type_chart.json")
        assert chart["fire"]["grass"] == 2.0

    def test_water_super_effective_on_fire(self):
        chart = _load_json("type_chart.json")
        assert chart["water"]["fire"] == 2.0

    def test_electric_immune_to_ground(self):
        chart = _load_json("type_chart.json")
        assert chart["electric"]["ground"] == 0.0

    def test_normal_immune_to_ghost(self):
        chart = _load_json("type_chart.json")
        assert chart["normal"]["ghost"] == 0.0

    def test_ghost_immune_to_normal(self):
        chart = _load_json("type_chart.json")
        assert chart["ghost"]["normal"] == 0.0

    def test_fighting_super_effective_on_normal(self):
        chart = _load_json("type_chart.json")
        assert chart["fighting"]["normal"] == 2.0

    def test_all_multipliers_valid(self):
        chart = _load_json("type_chart.json")
        valid = {0.0, 0.5, 2.0}
        for atk_type, matchups in chart.items():
            for def_type, mult in matchups.items():
                assert mult in valid, (
                    f"{atk_type} vs {def_type}: {mult} not in {valid}"
                )


# ──── Abilities ─────────────────────────────────────────────

class TestAbilities:
    def test_ability_count(self):
        abilities = _load_json("abilities.json")
        assert len(abilities) >= 51

    EXPECTED_NEW_ABILITIES = [
        "chlorophyll", "swift_swim", "sand_veil", "water_absorb",
        "flash_fire", "thick_fat", "pressure", "synchronize",
        "natural_cure", "run_away",
    ]

    @pytest.mark.parametrize("ability_id", EXPECTED_NEW_ABILITIES)
    def test_ability_exists(self, ability_id):
        abilities = _load_json("abilities.json")
        assert ability_id in abilities, f"Ability {ability_id} not found"
        assert "name" in abilities[ability_id]
        assert "description" in abilities[ability_id]


# ──── Secret Areas ──────────────────────────────────────────

class TestSecretAreas:
    def test_secret_area_count(self):
        areas = _load_json("secret_areas.json")
        assert len(areas) == 5

    def test_cerulean_cave_secret(self):
        areas = _load_json("secret_areas.json")
        found = next((a for a in areas if a["id"] == "cerulean_cave_secret"), None)
        assert found is not None
        assert found["trigger_map_id"] == "cerulean_cave_b1f"
        assert found["unlock_conditions"]["min_badges"] == 8

    def test_power_plant_generator(self):
        areas = _load_json("secret_areas.json")
        found = next((a for a in areas if a["id"] == "power_plant_generator"), None)
        assert found is not None
        assert found["trigger_map_id"] == "power_plant"

    def test_all_areas_have_required_fields(self):
        areas = _load_json("secret_areas.json")
        for area in areas:
            assert "id" in area
            assert "display_name" in area
            assert "trigger_map_id" in area
            assert "unlock_conditions" in area
            assert "discovery_message" in area


# ──── Counts Unchanged ──────────────────────────────────────

class TestCountsUnchanged:
    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151

    def test_items_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 75
