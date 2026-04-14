"""Tests for Sprint 38: Egg groups, egg moves, breeding mechanics.

These tests verify egg group assignments, egg move inheritance data,
and breeding system mechanics.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Egg Groups ───────────────────────────────────────────────

class TestEggGroups:
    def test_group_count(self):
        groups = _load_json("egg_groups.json")
        assert len(groups) == 15

    EXPECTED_GROUPS = [
        "monster", "water_1", "water_2", "water_3", "bug",
        "flying", "field", "fairy", "grass", "human_like",
        "mineral", "amorphous", "dragon", "ditto", "undiscovered",
    ]

    @pytest.mark.parametrize("group_id", EXPECTED_GROUPS)
    def test_group_exists(self, group_id):
        groups = _load_json("egg_groups.json")
        assert group_id in groups
        assert "name" in groups[group_id]
        assert "species" in groups[group_id]
        assert len(groups[group_id]["species"]) >= 1

    def test_ditto_only_ditto(self):
        groups = _load_json("egg_groups.json")
        assert groups["ditto"]["species"] == [132]

    def test_legendaries_undiscovered(self):
        groups = _load_json("egg_groups.json")
        undiscovered = groups["undiscovered"]["species"]
        for legendary in [144, 145, 146, 150, 151]:
            assert legendary in undiscovered

    def test_starters_in_monster(self):
        groups = _load_json("egg_groups.json")
        monster = groups["monster"]["species"]
        for starter in [1, 4, 7]:
            assert starter in monster

    def test_all_species_valid_range(self):
        groups = _load_json("egg_groups.json")
        for gid, group in groups.items():
            for sid in group["species"]:
                assert 1 <= sid <= 151, f"Group {gid} has invalid species {sid}"


# ──── Egg Moves ────────────────────────────────────────────────

class TestEggMoves:
    def test_species_count(self):
        egg_moves = _load_json("egg_moves.json")
        assert len(egg_moves) >= 20

    def test_all_moves_valid(self):
        egg_moves = _load_json("egg_moves.json")
        moves = _load_json("moves.json")
        for species, move_list in egg_moves.items():
            for move_name in move_list:
                assert move_name in moves, (
                    f"{species} egg move {move_name} not in move database"
                )

    def test_starters_have_egg_moves(self):
        egg_moves = _load_json("egg_moves.json")
        assert "Bulbasaur" in egg_moves
        assert "Charmander" in egg_moves
        assert "Squirtle" in egg_moves

    def test_each_species_has_moves(self):
        egg_moves = _load_json("egg_moves.json")
        for species, moves in egg_moves.items():
            assert len(moves) >= 2, f"{species} has too few egg moves"

    def test_pikachu_egg_moves(self):
        egg_moves = _load_json("egg_moves.json")
        assert "Pikachu" in egg_moves
        assert len(egg_moves["Pikachu"]) >= 2


# ──── Breeding Mechanics ──────────────────────────────────────

class TestBreedingMechanics:
    def test_file_exists(self):
        bm = _load_json("breeding_mechanics.json")
        assert "daycare" in bm
        assert "egg_cycles" in bm
        assert "compatibility" in bm

    def test_daycare_location(self):
        bm = _load_json("breeding_mechanics.json")
        assert bm["daycare"]["location"] == "route_5"

    def test_daycare_capacity(self):
        bm = _load_json("breeding_mechanics.json")
        assert bm["daycare"]["max_pokemon"] == 2

    def test_daycare_cost(self):
        bm = _load_json("breeding_mechanics.json")
        assert bm["daycare"]["cost_per_level"] == 100

    def test_steps_per_cycle(self):
        bm = _load_json("breeding_mechanics.json")
        assert bm["egg_cycles"]["steps_per_cycle"] == 256

    def test_cycle_ranges(self):
        bm = _load_json("breeding_mechanics.json")
        cycles = bm["egg_cycles"]["cycle_ranges"]
        assert len(cycles) >= 5
        for cycle_count, data in cycles.items():
            assert data["steps"] == int(cycle_count) * 256

    def test_magikarp_fastest_hatch(self):
        bm = _load_json("breeding_mechanics.json")
        cycles = bm["egg_cycles"]["cycle_ranges"]
        magikarp_cycles = next(
            c for c, d in cycles.items() if "Magikarp" in d["species_examples"]
        )
        assert int(magikarp_cycles) == 5

    def test_compatibility_levels(self):
        bm = _load_json("breeding_mechanics.json")
        compat = bm["compatibility"]
        assert compat["same_species_different_gender"]["chance_per_cycle"] > compat["same_egg_group_different_species"]["chance_per_cycle"]
        assert compat["incompatible"]["chance_per_cycle"] == 0

    def test_ditto_compatibility(self):
        bm = _load_json("breeding_mechanics.json")
        assert bm["compatibility"]["ditto_with_any"]["chance_per_cycle"] > 0

    def test_inheritance_rules(self):
        bm = _load_json("breeding_mechanics.json")
        inh = bm["inheritance"]
        assert "ivs" in inh
        assert "nature" in inh
        assert "ability" in inh
        assert "egg_moves" in inh


# ──── Counts ───────────────────────────────────────────────────

class TestCounts:
    def test_items_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 93

    def test_moves_unchanged(self):
        moves = _load_json("moves.json")
        assert len(moves) == 174

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151
