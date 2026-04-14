"""Tests for Sprint 55: Overworld animations, battle backgrounds, trainer AI patterns.

These tests verify overworld sprite animation data, battle scene backgrounds,
and trainer AI behavior pattern definitions.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Overworld Animations ───────────────────────────────────

class TestOverworldAnimations:
    def test_player_animation_count(self):
        oa = _load_json("overworld_animations.json")
        assert len(oa["player_animations"]) == 23

    def test_npc_animation_count(self):
        oa = _load_json("overworld_animations.json")
        assert len(oa["npc_animations"]) == 10

    def test_special_animation_count(self):
        oa = _load_json("overworld_animations.json")
        assert len(oa["special_animations"]) == 10

    def test_player_anims_have_fields(self):
        oa = _load_json("overworld_animations.json")
        for name, anim in oa["player_animations"].items():
            assert "frames" in anim, f"{name} missing frames"
            assert "frame_duration_ms" in anim, f"{name} missing frame_duration_ms"
            assert "loop" in anim, f"{name} missing loop"

    def test_walk_directions_exist(self):
        oa = _load_json("overworld_animations.json")
        pa = oa["player_animations"]
        for direction in ["up", "down", "left", "right"]:
            assert f"walk_{direction}" in pa
            assert f"idle_{direction}" in pa

    def test_run_animations_faster(self):
        oa = _load_json("overworld_animations.json")
        pa = oa["player_animations"]
        assert pa["run_up"]["frame_duration_ms"] < pa["walk_up"]["frame_duration_ms"]

    def test_special_anims_have_description(self):
        oa = _load_json("overworld_animations.json")
        for name, anim in oa["special_animations"].items():
            assert "description" in anim, f"{name} missing description"

    def test_sprite_config(self):
        oa = _load_json("overworld_animations.json")
        sc = oa["sprite_config"]
        assert sc["tile_size"] == 16
        assert sc["shadow_enabled"] is True
        assert sc["movement_speed_run"] > sc["movement_speed_walk"]

    def test_bike_faster_than_run(self):
        oa = _load_json("overworld_animations.json")
        sc = oa["sprite_config"]
        assert sc["movement_speed_bike"] > sc["movement_speed_run"]


# ──── Battle Backgrounds ─────────────────────────────────────

class TestBattleBackgrounds:
    def test_background_count(self):
        bb = _load_json("battle_backgrounds.json")
        assert len(bb["backgrounds"]) == 18

    def test_backgrounds_have_fields(self):
        bb = _load_json("battle_backgrounds.json")
        for name, bg in bb["backgrounds"].items():
            assert "display_name" in bg, f"{name} missing display_name"
            assert "base_color" in bg, f"{name} missing base_color"
            assert "ground_pattern" in bg, f"{name} missing ground_pattern"
            assert "horizon_y" in bg, f"{name} missing horizon_y"
            assert "elements" in bg, f"{name} missing elements"

    def test_base_colors_valid(self):
        bb = _load_json("battle_backgrounds.json")
        import re
        hex_pat = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for name, bg in bb["backgrounds"].items():
            assert hex_pat.match(bg["base_color"]), f"{name} bad base_color"

    def test_horizon_in_range(self):
        bb = _load_json("battle_backgrounds.json")
        for name, bg in bb["backgrounds"].items():
            assert 0.0 < bg["horizon_y"] < 1.0, f"{name} horizon_y out of range"

    def test_gym_backgrounds_exist(self):
        bb = _load_json("battle_backgrounds.json")
        gym_types = ["gym_rock", "gym_water", "gym_electric", "gym_grass",
                     "gym_poison", "gym_psychic", "gym_fire", "gym_ground"]
        for gt in gym_types:
            assert gt in bb["backgrounds"], f"Missing {gt} background"

    def test_elite_four_background(self):
        bb = _load_json("battle_backgrounds.json")
        assert "elite_four_chamber" in bb["backgrounds"]

    def test_backgrounds_have_used_in(self):
        bb = _load_json("battle_backgrounds.json")
        for name, bg in bb["backgrounds"].items():
            assert "used_in" in bg, f"{name} missing used_in"

    def test_config_present(self):
        bb = _load_json("battle_backgrounds.json")
        cfg = bb["background_config"]
        assert cfg["width"] > 0
        assert cfg["height"] > 0
        assert "parallax_enabled" in cfg


# ──── Trainer AI Patterns ────────────────────────────────────

class TestTrainerAIPatterns:
    def test_pattern_count(self):
        ta = _load_json("trainer_ai_patterns.json")
        assert len(ta["patterns"]) == 16

    def test_strategy_count(self):
        ta = _load_json("trainer_ai_patterns.json")
        assert len(ta["strategies"]) == 5

    def test_move_selection_count(self):
        ta = _load_json("trainer_ai_patterns.json")
        assert len(ta["move_selection_methods"]) == 4

    def test_patterns_have_fields(self):
        ta = _load_json("trainer_ai_patterns.json")
        required = ["class_id", "strategy", "move_selection", "switch_threshold_hp_pct",
                     "use_items", "predict_player_switch", "description"]
        for name, pattern in ta["patterns"].items():
            for field in required:
                assert field in pattern, f"{name} missing {field}"

    def test_patterns_reference_valid_strategies(self):
        ta = _load_json("trainer_ai_patterns.json")
        valid_strats = set(ta["strategies"].keys())
        for name, pattern in ta["patterns"].items():
            assert pattern["strategy"] in valid_strats, \
                f"{name} invalid strategy: {pattern['strategy']}"

    def test_patterns_reference_valid_selection(self):
        ta = _load_json("trainer_ai_patterns.json")
        valid_methods = set(ta["move_selection_methods"].keys())
        for name, pattern in ta["patterns"].items():
            assert pattern["move_selection"] in valid_methods, \
                f"{name} invalid move_selection: {pattern['move_selection']}"

    def test_class_ids_match_trainer_classes(self):
        ta = _load_json("trainer_ai_patterns.json")
        tc = _load_json("trainer_classes.json")
        tc_ids = set(tc.keys())
        for name, pattern in ta["patterns"].items():
            assert pattern["class_id"] in tc_ids, \
                f"{name} class_id {pattern['class_id']} not in trainer_classes"

    def test_champion_is_expert(self):
        ta = _load_json("trainer_ai_patterns.json")
        assert ta["patterns"]["champion"]["strategy"] == "expert"
        assert ta["patterns"]["champion"]["use_items"] is True
        assert ta["patterns"]["champion"]["predict_player_switch"] is True

    def test_youngster_is_aggressive(self):
        ta = _load_json("trainer_ai_patterns.json")
        assert ta["patterns"]["youngster"]["strategy"] == "aggressive"
        assert ta["patterns"]["youngster"]["use_items"] is False

    def test_switch_threshold_range(self):
        ta = _load_json("trainer_ai_patterns.json")
        for name, pattern in ta["patterns"].items():
            assert 0 < pattern["switch_threshold_hp_pct"] <= 50, \
                f"{name} threshold out of range: {pattern['switch_threshold_hp_pct']}"


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
