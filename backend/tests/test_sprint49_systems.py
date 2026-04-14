"""Tests for Sprint 49: Catch rate formula, happiness system, battle tower.

These tests verify catch probability calculations, friendship mechanics,
and battle tower facility configuration.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Catch Rate Formula ─────────────────────────────────────

class TestCatchRateFormula:
    def test_has_formula(self):
        cr = _load_json("catch_rate_formula.json")
        assert "formula" in cr
        assert "description" in cr["formula"]

    def test_ball_modifiers(self):
        cr = _load_json("catch_rate_formula.json")
        balls = cr["ball_modifiers"]
        assert len(balls) >= 5
        assert balls["poke_ball"]["modifier"] == 1.0
        assert balls["great_ball"]["modifier"] == 1.5
        assert balls["ultra_ball"]["modifier"] == 2.0
        assert balls["master_ball"]["modifier"] == 255

    def test_status_modifiers(self):
        cr = _load_json("catch_rate_formula.json")
        status = cr["status_modifiers"]
        assert status["none"] == 1.0
        assert status["sleep"] == 2.5
        assert status["freeze"] == 2.5
        assert status["paralysis"] == 1.5

    def test_catch_rate_examples(self):
        cr = _load_json("catch_rate_formula.json")
        examples = cr["catch_rates"]["common_examples"]
        assert examples["Caterpie"] == 255
        assert examples["Mewtwo"] == 3
        assert examples["Pikachu"] == 190

    def test_catch_rate_ranges(self):
        cr = _load_json("catch_rate_formula.json")
        ranges = cr["catch_rates"]["ranges"]
        assert len(ranges) >= 5
        assert ranges["very_easy"]["max"] == 255
        assert ranges["very_hard"]["min"] == 3

    def test_safari_zone_modifiers(self):
        cr = _load_json("catch_rate_formula.json")
        safari = cr["safari_zone"]
        assert safari["bait_catch_modifier"] == 0.5
        assert safari["rock_catch_modifier"] == 2.0
        assert safari["bait_flee_modifier"] == 0.5
        assert safari["rock_flee_modifier"] == 2.0

    def test_hp_factor(self):
        cr = _load_json("catch_rate_formula.json")
        hp = cr["hp_factor"]
        assert hp["full_hp_factor"] < hp["half_hp_factor"]
        assert hp["half_hp_factor"] < hp["one_hp_factor"]

    def test_shakes_needed(self):
        cr = _load_json("catch_rate_formula.json")
        assert cr["formula"]["shakes_needed"] == 4


# ──── Happiness System ────────────────────────────────────────

class TestHappinessSystem:
    def test_base_happiness(self):
        hs = _load_json("happiness_system.json")
        assert hs["base_happiness"] == 70

    def test_happiness_range(self):
        hs = _load_json("happiness_system.json")
        assert hs["min_happiness"] == 0
        assert hs["max_happiness"] == 255

    def test_evolution_threshold(self):
        hs = _load_json("happiness_system.json")
        assert hs["evolution_threshold"] == 220

    def test_positive_events(self):
        hs = _load_json("happiness_system.json")
        events = hs["events"]
        assert events["level_up"]["change"] > 0
        assert events["walk_256_steps"]["change"] > 0
        assert events["vitamin_used"]["change"] > 0

    def test_negative_events(self):
        hs = _load_json("happiness_system.json")
        events = hs["events"]
        assert events["faint"]["change"] < 0
        assert events["bitter_medicine"]["change"] < 0
        assert events["revival_herb"]["change"] < 0

    def test_friendship_evolutions(self):
        hs = _load_json("happiness_system.json")
        evos = hs["friendship_evolutions"]
        assert len(evos) >= 5

    def test_eevee_time_split(self):
        hs = _load_json("happiness_system.json")
        evos = hs["friendship_evolutions"]
        eevee_evos = [e for e in evos if e["species"] == "Eevee"]
        assert len(eevee_evos) >= 2

    def test_return_power(self):
        hs = _load_json("happiness_system.json")
        ret = hs["move_power"]["return"]
        assert ret["max_power"] == 102
        assert ret["min_power"] == 1

    def test_frustration_power(self):
        hs = _load_json("happiness_system.json")
        frust = hs["move_power"]["frustration"]
        assert frust["max_power"] == 102

    def test_soothe_bell(self):
        hs = _load_json("happiness_system.json")
        assert hs["soothe_bell"]["happiness_multiplier"] == 1.5

    def test_traded_pokemon_penalty(self):
        hs = _load_json("happiness_system.json")
        assert hs["ot_bonus"]["traded_pokemon_multiplier"] < 1.0


# ──── Battle Tower ────────────────────────────────────────────

class TestBattleTower:
    def test_location(self):
        bt = _load_json("battle_tower.json")
        assert bt["location"] == "indigo_plateau"

    def test_unlock_condition(self):
        bt = _load_json("battle_tower.json")
        assert bt["unlock_condition"] == "become_champion"

    def test_rules(self):
        bt = _load_json("battle_tower.json")
        rules = bt["rules"]
        assert rules["level_cap"] == 50
        assert rules["party_size"] == 3
        assert rules["no_duplicate_species"] is True
        assert rules["sleep_clause"] is True

    def test_banned_species(self):
        bt = _load_json("battle_tower.json")
        banned = bt["rules"]["banned_species"]
        assert "Mewtwo" in banned
        assert "Mew" in banned

    def test_streaks(self):
        bt = _load_json("battle_tower.json")
        streaks = bt["streaks"]
        assert streaks["battles_per_streak"] == 7
        assert streaks["frontier_brain_battle"] == 21

    def test_difficulty_scaling(self):
        bt = _load_json("battle_tower.json")
        scaling = bt["difficulty_scaling"]
        assert len(scaling) >= 4
        first = scaling["battles_1_to_7"]
        last = scaling["battles_22_plus"]
        assert first["min_level"] < last["min_level"]

    def test_rewards(self):
        bt = _load_json("battle_tower.json")
        rewards = bt["rewards"]
        assert rewards["per_battle"]["bp"] == 1
        assert rewards["streak_7"]["bp"] > rewards["per_battle"]["bp"]
        assert rewards["streak_49"]["bp"] > rewards["streak_21"]["bp"]

    def test_bp_shop(self):
        bt = _load_json("battle_tower.json")
        shop = bt["bp_shop"]
        assert len(shop) >= 10
        for item in shop:
            assert "item" in item
            assert "cost_bp" in item
            assert item["cost_bp"] > 0

    def test_trainer_pool(self):
        bt = _load_json("battle_tower.json")
        pool = bt["trainer_pool"]
        assert len(pool["classes"]) >= 5
        gen = pool["team_generation"]
        assert gen["min_team_size"] == 3
        assert gen["max_team_size"] == 3
        assert gen["ev_total"] == 510


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
