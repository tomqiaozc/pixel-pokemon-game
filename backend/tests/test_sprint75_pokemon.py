"""Tests for Sprint 75: Stat calculation, nickname system, move categories.

These tests verify stat formulas, nickname configuration,
and move category mechanics.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Stat Calculation ───────────────────────────────────────

class TestStatCalculation:
    def test_hp_formula_defined(self):
        sc = _load_json("stat_calculation.json")
        assert "hp_formula" in sc
        assert "description" in sc["hp_formula"]

    def test_other_stat_formula_defined(self):
        sc = _load_json("stat_calculation.json")
        assert "other_stat_formula" in sc
        assert "nature" in sc["other_stat_formula"]["components"]

    def test_iv_range(self):
        sc = _load_json("stat_calculation.json")
        iv = sc["iv_config"]
        assert iv["min"] == 0
        assert iv["max"] == 31

    def test_iv_six_stats(self):
        sc = _load_json("stat_calculation.json")
        assert len(sc["iv_config"]["stats_with_iv"]) == 6

    def test_ev_limits(self):
        sc = _load_json("stat_calculation.json")
        ev = sc["ev_config"]
        assert ev["max_per_stat"] == 252
        assert ev["max_total"] == 510

    def test_ev_4_per_point(self):
        sc = _load_json("stat_calculation.json")
        assert sc["ev_config"]["ev_per_4_equals_1_stat_point"] is True

    def test_nature_multipliers(self):
        sc = _load_json("stat_calculation.json")
        nm = sc["nature_multipliers"]
        assert nm["positive"] == 1.1
        assert nm["negative"] == 0.9
        assert nm["neutral"] == 1.0
        assert nm["total_natures"] == 25

    def test_level_range(self):
        sc = _load_json("stat_calculation.json")
        assert sc["level_range"]["min"] == 1
        assert sc["level_range"]["max"] == 100


# ──── Nickname System ────────────────────────────────────────

class TestNicknameSystem:
    def test_max_nickname_length(self):
        ns = _load_json("nickname_system.json")
        assert ns["max_nickname_length"] == 10

    def test_name_rater_location(self):
        ns = _load_json("nickname_system.json")
        nr = ns["name_rater"]
        assert nr["location"] == "lavender_town"
        assert nr["free_service"] is True

    def test_cannot_rename_traded(self):
        ns = _load_json("nickname_system.json")
        assert ns["name_rater"]["cannot_rename_traded"] is True

    def test_prompt_on_capture(self):
        ns = _load_json("nickname_system.json")
        assert ns["naming_rules"]["prompt_on_capture"] is True

    def test_can_skip(self):
        ns = _load_json("nickname_system.json")
        assert ns["naming_rules"]["can_skip_naming"] is True

    def test_keyboard_qwerty(self):
        ns = _load_json("nickname_system.json")
        kb = ns["keyboard_layout"]
        assert kb["type"] == "QWERTY"
        assert len(kb["pages"]) == 2

    def test_evolved_keeps_nickname(self):
        ns = _load_json("nickname_system.json")
        assert ns["special_cases"]["evolved_keeps_nickname"] is True

    def test_traded_keeps_name(self):
        ns = _load_json("nickname_system.json")
        assert ns["special_cases"]["traded_keeps_name"] is True


# ──── Move Categories ────────────────────────────────────────

class TestMoveCategories:
    def test_three_categories(self):
        mc = _load_json("move_categories.json")
        assert len(mc["categories"]) == 3
        assert mc["total_categories"] == 3

    def test_category_names(self):
        mc = _load_json("move_categories.json")
        assert "physical" in mc["categories"]
        assert "special" in mc["categories"]
        assert "status" in mc["categories"]

    def test_physical_uses_attack(self):
        mc = _load_json("move_categories.json")
        assert mc["categories"]["physical"]["stat_used"] == "attack"
        assert mc["categories"]["physical"]["defense_used"] == "defense"

    def test_special_uses_sp_attack(self):
        mc = _load_json("move_categories.json")
        assert mc["categories"]["special"]["stat_used"] == "sp_attack"

    def test_recoil_moves(self):
        mc = _load_json("move_categories.json")
        recoil = mc["special_mechanics"]["recoil_moves"]
        assert len(recoil) == 4
        assert mc["total_recoil_moves"] == 4
        names = [m["move"] for m in recoil]
        assert "Double Edge" in names

    def test_drain_moves(self):
        mc = _load_json("move_categories.json")
        drain = mc["special_mechanics"]["drain_moves"]
        assert len(drain) == 4
        for d in drain:
            assert d["drain_percent"] == 50

    def test_two_turn_moves(self):
        mc = _load_json("move_categories.json")
        tt = mc["special_mechanics"]["two_turn_moves"]
        assert len(tt) == 6
        names = [m["move"] for m in tt]
        assert "Solar Beam" in names
        assert "Fly" in names
        assert "Dig" in names

    def test_ohko_moves(self):
        mc = _load_json("move_categories.json")
        ohko = mc["special_mechanics"]["ohko_moves"]
        assert len(ohko) == 3
        for o in ohko:
            assert o["fails_if_lower_level"] is True

    def test_self_destruct_moves(self):
        mc = _load_json("move_categories.json")
        sd = mc["special_mechanics"]["self_destruct_moves"]
        assert len(sd) == 2
        for s in sd:
            assert s["user_faints"] is True

    def test_recoil_moves_in_moves_json(self):
        mc = _load_json("move_categories.json")
        moves = _load_json("moves.json")
        for rm in mc["special_mechanics"]["recoil_moves"]:
            if rm["move"] != "Struggle":
                assert rm["move"] in moves


# ──── Counts ──────────────────────────────────────────────────

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
