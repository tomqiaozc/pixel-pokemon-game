"""Tests for Sprint 32: Natures, status conditions, EV/IV system.

These tests verify the 25 natures with stat modifiers, 9 status conditions,
and the EV/IV stat system definitions.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Natures ──────────────────────────────────────────────────

class TestNatures:
    def test_nature_count(self):
        natures = _load_json("natures.json")
        assert len(natures) == 25

    NEUTRAL_NATURES = ["hardy", "docile", "serious", "bashful", "quirky"]

    @pytest.mark.parametrize("nature_id", NEUTRAL_NATURES)
    def test_neutral_natures(self, nature_id):
        natures = _load_json("natures.json")
        n = natures[nature_id]
        assert n["increased_stat"] is None
        assert n["decreased_stat"] is None

    STAT_NATURES = [
        ("adamant", "attack", "sp_attack"),
        ("bold", "defense", "attack"),
        ("timid", "speed", "attack"),
        ("modest", "sp_attack", "attack"),
        ("calm", "sp_defense", "attack"),
        ("jolly", "speed", "sp_attack"),
        ("brave", "attack", "speed"),
    ]

    @pytest.mark.parametrize("nature_id,up,down", STAT_NATURES)
    def test_stat_modifying_natures(self, nature_id, up, down):
        natures = _load_json("natures.json")
        n = natures[nature_id]
        assert n["increased_stat"] == up
        assert n["decreased_stat"] == down

    def test_all_natures_have_name(self):
        natures = _load_json("natures.json")
        for nid, nature in natures.items():
            assert "name" in nature
            assert len(nature["name"]) > 0

    VALID_STATS = {"attack", "defense", "sp_attack", "sp_defense", "speed"}

    def test_all_stat_references_valid(self):
        natures = _load_json("natures.json")
        for nid, nature in natures.items():
            if nature["increased_stat"] is not None:
                assert nature["increased_stat"] in self.VALID_STATS
            if nature["decreased_stat"] is not None:
                assert nature["decreased_stat"] in self.VALID_STATS

    def test_no_nature_boosts_and_lowers_same_stat(self):
        natures = _load_json("natures.json")
        for nid, nature in natures.items():
            if nature["increased_stat"] is not None:
                assert nature["increased_stat"] != nature["decreased_stat"]

    def test_exactly_5_neutral_natures(self):
        natures = _load_json("natures.json")
        neutral = [n for n in natures.values() if n["increased_stat"] is None]
        assert len(neutral) == 5


# ──── Status Conditions ────────────────────────────────────────

class TestStatusConditions:
    def test_status_count(self):
        conditions = _load_json("status_conditions.json")
        assert len(conditions) == 9

    NON_VOLATILE = ["burn", "poison", "badly_poisoned", "paralysis", "sleep", "freeze"]
    VOLATILE = ["confusion", "flinch", "infatuation"]

    @pytest.mark.parametrize("status_id", NON_VOLATILE)
    def test_non_volatile_conditions(self, status_id):
        conditions = _load_json("status_conditions.json")
        assert conditions[status_id]["type"] == "non_volatile"

    @pytest.mark.parametrize("status_id", VOLATILE)
    def test_volatile_conditions(self, status_id):
        conditions = _load_json("status_conditions.json")
        assert conditions[status_id]["type"] == "volatile"

    def test_burn_reduces_attack(self):
        conditions = _load_json("status_conditions.json")
        assert conditions["burn"]["attack_modifier"] == 0.5

    def test_burn_damages_per_turn(self):
        conditions = _load_json("status_conditions.json")
        assert conditions["burn"]["damage_per_turn_percent"] == 6.25

    def test_paralysis_reduces_speed(self):
        conditions = _load_json("status_conditions.json")
        assert conditions["paralysis"]["speed_modifier"] == 0.25

    def test_paralysis_cant_move_chance(self):
        conditions = _load_json("status_conditions.json")
        assert conditions["paralysis"]["cant_move_chance"] == 25

    def test_sleep_has_turn_range(self):
        conditions = _load_json("status_conditions.json")
        slp = conditions["sleep"]
        assert slp["min_turns"] == 1
        assert slp["max_turns"] == 3

    def test_freeze_thaw_on_fire(self):
        conditions = _load_json("status_conditions.json")
        assert conditions["freeze"]["thaw_on_fire_move"] is True

    def test_badly_poisoned_increments(self):
        conditions = _load_json("status_conditions.json")
        bp = conditions["badly_poisoned"]
        assert bp["damage_per_turn_start"] == 6.25
        assert bp["damage_increment"] == 6.25

    def test_confusion_self_hit(self):
        conditions = _load_json("status_conditions.json")
        cnf = conditions["confusion"]
        assert cnf["self_hit_chance"] == 33
        assert cnf["self_hit_power"] == 40

    def test_all_conditions_have_required_fields(self):
        conditions = _load_json("status_conditions.json")
        for sid, cond in conditions.items():
            assert "name" in cond
            assert "abbreviation" in cond
            assert "type" in cond

    def test_all_have_cured_by(self):
        conditions = _load_json("status_conditions.json")
        for sid, cond in conditions.items():
            assert "cured_by" in cond
            assert isinstance(cond["cured_by"], list)


# ──── EV/IV System ─────────────────────────────────────────────

class TestEVIVSystem:
    def test_system_file_exists(self):
        system = _load_json("ev_iv_system.json")
        assert "ivs" in system
        assert "evs" in system

    def test_iv_range(self):
        system = _load_json("ev_iv_system.json")
        assert system["ivs"]["min_value"] == 0
        assert system["ivs"]["max_value"] == 31

    def test_ev_caps(self):
        system = _load_json("ev_iv_system.json")
        assert system["evs"]["max_value_per_stat"] == 252
        assert system["evs"]["max_total"] == 510

    def test_six_stats_covered(self):
        system = _load_json("ev_iv_system.json")
        expected = {"hp", "attack", "defense", "sp_attack", "sp_defense", "speed"}
        assert set(system["ivs"]["stats"]) == expected
        assert set(system["evs"]["stats"]) == expected

    def test_nature_modifiers(self):
        system = _load_json("ev_iv_system.json")
        nm = system["nature_modifier"]
        assert nm["increased"] == 1.1
        assert nm["decreased"] == 0.9
        assert nm["neutral"] == 1.0

    def test_stat_formulas_present(self):
        system = _load_json("ev_iv_system.json")
        assert "hp" in system["stat_formula"]
        assert "other" in system["stat_formula"]

    def test_vitamin_data(self):
        system = _load_json("ev_iv_system.json")
        vitamins = system["vitamins"]
        assert len(vitamins) == 6
        for name, data in vitamins.items():
            assert "stat" in data
            assert data["ev_gain"] == 10

    def test_ev_yield_examples(self):
        system = _load_json("ev_iv_system.json")
        yields = system["evs"]["ev_yield_examples"]
        assert len(yields) >= 10
        assert yields["charmander"] == {"speed": 1}
        assert yields["geodude"] == {"defense": 1}


# ──── Counts ───────────────────────────────────────────────────

class TestCounts:
    def test_items_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 93

    def test_moves_unchanged(self):
        moves = _load_json("moves.json")
        assert len(moves) == 174

    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151
