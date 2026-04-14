"""Tests for Sprint 33: Battle mechanics, trainer classes, experience groups.

These tests verify damage formula data, critical hit rates, stat stages,
trainer class definitions, and experience growth curves.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Battle Mechanics ─────────────────────────────────────────

class TestBattleMechanics:
    def test_file_exists(self):
        mechanics = _load_json("battle_mechanics.json")
        assert "damage_formula" in mechanics

    def test_stab_multiplier(self):
        mechanics = _load_json("battle_mechanics.json")
        assert mechanics["damage_formula"]["stab_multiplier"] == 1.5

    def test_critical_hit_multiplier(self):
        mechanics = _load_json("battle_mechanics.json")
        assert mechanics["damage_formula"]["critical_hit_multiplier"] == 1.5

    def test_random_range(self):
        mechanics = _load_json("battle_mechanics.json")
        rng = mechanics["damage_formula"]["random_range"]
        assert rng["min"] == 0.85
        assert rng["max"] == 1.0

    def test_minimum_damage(self):
        mechanics = _load_json("battle_mechanics.json")
        assert mechanics["damage_formula"]["minimum_damage"] == 1

    def test_crit_stages(self):
        mechanics = _load_json("battle_mechanics.json")
        stages = mechanics["critical_hit_stages"]
        assert stages["0"] == 6.25
        assert stages["1"] == 12.5
        assert stages["4"] == 50.0

    def test_accuracy_stage_0_is_100(self):
        mechanics = _load_json("battle_mechanics.json")
        assert mechanics["accuracy_stages"]["0"] == 100.0

    def test_accuracy_stage_negative(self):
        mechanics = _load_json("battle_mechanics.json")
        assert mechanics["accuracy_stages"]["-6"] == 33.33

    def test_stat_stage_0_is_1(self):
        mechanics = _load_json("battle_mechanics.json")
        assert mechanics["stat_stages"]["0"] == 1.0

    def test_stat_stage_positive(self):
        mechanics = _load_json("battle_mechanics.json")
        assert mechanics["stat_stages"]["6"] == 4.0

    def test_stat_stage_negative(self):
        mechanics = _load_json("battle_mechanics.json")
        assert mechanics["stat_stages"]["-6"] == 0.25

    def test_type_effectiveness_values(self):
        mechanics = _load_json("battle_mechanics.json")
        te = mechanics["type_effectiveness"]
        assert te["super_effective"] == 2.0
        assert te["not_very_effective"] == 0.5
        assert te["immune"] == 0.0
        assert te["neutral"] == 1.0

    def test_multi_hit_distribution(self):
        mechanics = _load_json("battle_mechanics.json")
        dist = mechanics["multi_hit_distribution"]
        total = sum(dist.values())
        assert total == 100.0


# ──── Trainer Classes ──────────────────────────────────────────

class TestTrainerClasses:
    def test_class_count(self):
        classes = _load_json("trainer_classes.json")
        assert len(classes) == 26

    EXPECTED_CLASSES = [
        "youngster", "lass", "bug_catcher", "hiker",
        "fisherman", "beauty", "blackbelt", "rocket_grunt",
        "gym_leader", "elite_four", "champion",
    ]

    @pytest.mark.parametrize("class_id", EXPECTED_CLASSES)
    def test_class_exists(self, class_id):
        classes = _load_json("trainer_classes.json")
        assert class_id in classes
        c = classes[class_id]
        assert "name" in c
        assert "prize_per_level" in c
        assert "sprite" in c

    def test_all_have_prize_money(self):
        classes = _load_json("trainer_classes.json")
        for cid, cls in classes.items():
            assert cls["prize_per_level"] > 0, f"{cid} has no prize money"

    def test_champion_highest_prize(self):
        classes = _load_json("trainer_classes.json")
        champ_prize = classes["champion"]["prize_per_level"]
        for cid, cls in classes.items():
            if cid != "champion":
                assert cls["prize_per_level"] <= champ_prize

    def test_gym_leader_high_prize(self):
        classes = _load_json("trainer_classes.json")
        assert classes["gym_leader"]["prize_per_level"] >= 100

    def test_elite_four_high_prize(self):
        classes = _load_json("trainer_classes.json")
        assert classes["elite_four"]["prize_per_level"] >= 120


# ──── Experience Groups ────────────────────────────────────────

class TestExperienceGroups:
    def test_group_count(self):
        groups = _load_json("experience_groups.json")
        assert len(groups) == 4

    EXPECTED_GROUPS = ["fast", "medium_fast", "medium_slow", "slow"]

    @pytest.mark.parametrize("group_id", EXPECTED_GROUPS)
    def test_group_exists(self, group_id):
        groups = _load_json("experience_groups.json")
        assert group_id in groups
        g = groups[group_id]
        assert "name" in g
        assert "formula" in g
        assert "level_100_exp" in g
        assert "pokemon_examples" in g

    def test_fast_less_than_medium(self):
        groups = _load_json("experience_groups.json")
        assert groups["fast"]["level_100_exp"] < groups["medium_fast"]["level_100_exp"]

    def test_slow_most_exp(self):
        groups = _load_json("experience_groups.json")
        assert groups["slow"]["level_100_exp"] == 1250000

    def test_medium_fast_standard(self):
        groups = _load_json("experience_groups.json")
        assert groups["medium_fast"]["level_100_exp"] == 1000000

    def test_starters_in_medium_fast(self):
        groups = _load_json("experience_groups.json")
        examples = groups["medium_fast"]["pokemon_examples"]
        for starter in ["Bulbasaur", "Charmander", "Squirtle"]:
            assert starter in examples

    def test_all_groups_have_examples(self):
        groups = _load_json("experience_groups.json")
        for gid, group in groups.items():
            assert len(group["pokemon_examples"]) >= 2


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

    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132
