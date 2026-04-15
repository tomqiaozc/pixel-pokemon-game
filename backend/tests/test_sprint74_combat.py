"""Tests for Sprint 74: Type matchup details, wild battle rules, catch tutorial.

These tests verify type interaction data, wild encounter mechanics,
and the Old Man catch tutorial event.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Type Matchup Details ───────────────────────────────────

class TestTypeMatchupDetails:
    def test_type_count(self):
        tm = _load_json("type_matchup_details.json")
        assert len(tm["types"]) == 15

    def test_total_types_match(self):
        tm = _load_json("type_matchup_details.json")
        assert tm["total_types"] == len(tm["types"])

    def test_types_have_fields(self):
        tm = _load_json("type_matchup_details.json")
        for t in tm["types"]:
            assert "name" in t
            assert "super_effective_against" in t
            assert "weak_to" in t
            assert "resists" in t
            assert "immune_to" in t

    def test_ground_immune_to_electric(self):
        tm = _load_json("type_matchup_details.json")
        ground = next(t for t in tm["types"] if t["name"] == "Ground")
        assert "Electric" in ground["immune_to"]

    def test_ghost_immune_to_normal(self):
        tm = _load_json("type_matchup_details.json")
        ghost = next(t for t in tm["types"] if t["name"] == "Ghost")
        assert "Normal" in ghost["immune_to"]

    def test_flying_immune_to_ground(self):
        tm = _load_json("type_matchup_details.json")
        flying = next(t for t in tm["types"] if t["name"] == "Flying")
        assert "Ground" in flying["immune_to"]

    def test_no_steel_dark_fairy(self):
        tm = _load_json("type_matchup_details.json")
        notes = tm["gen1_notes"]
        assert notes["no_steel_type"] is True
        assert notes["no_dark_type"] is True
        assert notes["no_fairy_type"] is True

    def test_dragon_weak_to_ice(self):
        tm = _load_json("type_matchup_details.json")
        dragon = next(t for t in tm["types"] if t["name"] == "Dragon")
        assert "Ice" in dragon["weak_to"]

    def test_psychic_weak_to_bug(self):
        tm = _load_json("type_matchup_details.json")
        psychic = next(t for t in tm["types"] if t["name"] == "Psychic")
        assert "Bug" in psychic["weak_to"]


# ──── Wild Battle Rules ──────────────────────────────────────

class TestWildBattleRules:
    def test_battle_options_count(self):
        wb = _load_json("wild_battle_rules.json")
        assert len(wb["battle_options"]) == 4

    def test_total_options_match(self):
        wb = _load_json("wild_battle_rules.json")
        assert wb["total_battle_options"] == len(wb["battle_options"])

    def test_four_actions(self):
        wb = _load_json("wild_battle_rules.json")
        actions = [o["action"] for o in wb["battle_options"]]
        assert "fight" in actions
        assert "bag" in actions
        assert "pokemon" in actions
        assert "run" in actions

    def test_encounter_triggers(self):
        wb = _load_json("wild_battle_rules.json")
        triggers = wb["encounter_trigger"]
        assert "grass" in triggers
        assert "cave" in triggers
        assert "water" in triggers
        assert "fishing" in triggers

    def test_wild_pokemon_no_items(self):
        wb = _load_json("wild_battle_rules.json")
        assert wb["wild_pokemon_rules"]["no_items"] is True

    def test_wild_no_money(self):
        wb = _load_json("wild_battle_rules.json")
        assert wb["wild_pokemon_rules"]["money_given"] is False

    def test_exp_on_capture(self):
        wb = _load_json("wild_battle_rules.json")
        assert wb["wild_pokemon_rules"]["exp_given_on_capture"] is True

    def test_repel_blocks_lower_level(self):
        wb = _load_json("wild_battle_rules.json")
        repel = wb["repel_interaction"]
        assert repel["blocks_encounters"] is True
        assert repel["level_based"] is True
        assert repel["does_not_block_static"] is True

    def test_shiny_odds(self):
        wb = _load_json("wild_battle_rules.json")
        shiny = wb["shiny_odds"]
        assert shiny["denominator"] == 8192

    def test_flee_formula(self):
        wb = _load_json("wild_battle_rules.json")
        flee = wb["flee_formula"]
        assert "Poke Doll" in flee["guaranteed_flee_items"]
        assert flee["escape_attempts_increase_chance"] is True


# ──── Catch Tutorial ─────────────────────────────────────────

class TestCatchTutorial:
    def test_tutorial_steps(self):
        ct = _load_json("catch_tutorial.json")
        assert len(ct["tutorial_steps"]) == 8

    def test_total_steps_match(self):
        ct = _load_json("catch_tutorial.json")
        assert ct["total_steps"] == len(ct["tutorial_steps"])

    def test_location(self):
        ct = _load_json("catch_tutorial.json")
        assert ct["location"] == "viridian_city"
        assert ct["npc"] == "Old Man"

    def test_prerequisite(self):
        ct = _load_json("catch_tutorial.json")
        assert ct["prerequisite"] == "deliver_parcel_to_oak"

    def test_one_time(self):
        ct = _load_json("catch_tutorial.json")
        assert ct["one_time"] is True

    def test_capture_always_succeeds(self):
        ct = _load_json("catch_tutorial.json")
        capture_step = next(s for s in ct["tutorial_steps"] if s["action"] == "capture")
        assert capture_step["always_succeeds"] is True

    def test_pokemon_not_added(self):
        ct = _load_json("catch_tutorial.json")
        assert ct["rewards"]["pokemon_not_added_to_party"] is True


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
