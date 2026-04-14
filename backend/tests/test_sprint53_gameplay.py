"""Tests for Sprint 53: Time events, battle animations, control bindings.

These tests verify time-based events, battle visual animations,
and input configuration data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Time Events ────────────────────────────────────────────

class TestTimeEvents:
    def test_time_period_count(self):
        te = _load_json("time_events.json")
        assert len(te["time_periods"]) == 5

    def test_time_periods_have_fields(self):
        te = _load_json("time_events.json")
        for name, period in te["time_periods"].items():
            assert "start_hour" in period, f"{name} missing start_hour"
            assert "end_hour" in period, f"{name} missing end_hour"
            assert "sky_color" in period, f"{name} missing sky_color"
            assert "ambient_light" in period, f"{name} missing ambient_light"

    def test_ambient_light_range(self):
        te = _load_json("time_events.json")
        for name, period in te["time_periods"].items():
            assert 0.0 <= period["ambient_light"] <= 1.0, \
                f"{name} light {period['ambient_light']} out of range"

    def test_timed_encounter_count(self):
        te = _load_json("time_events.json")
        assert len(te["timed_encounters"]) == 12

    def test_timed_encounters_have_fields(self):
        te = _load_json("time_events.json")
        for enc in te["timed_encounters"]:
            assert "pokemon" in enc
            assert "location" in enc
            assert "time_period" in enc
            assert "level_range" in enc
            assert "rate_boost" in enc

    def test_timed_encounters_valid_periods(self):
        te = _load_json("time_events.json")
        valid = set(te["time_periods"].keys())
        for enc in te["timed_encounters"]:
            assert enc["time_period"] in valid, \
                f"{enc['pokemon']} has invalid period: {enc['time_period']}"

    def test_timed_encounters_valid_pokemon(self):
        te = _load_json("time_events.json")
        species = _load_json("pokemon_species.json")
        species_names = {s["name"] for s in species}
        for enc in te["timed_encounters"]:
            assert enc["pokemon"] in species_names, \
                f"{enc['pokemon']} not in species"

    def test_shop_hours_count(self):
        te = _load_json("time_events.json")
        assert len(te["shop_hours"]) == 4

    def test_pokecenter_always_open(self):
        te = _load_json("time_events.json")
        assert te["shop_hours"]["pokecenter"]["always_open"] is True

    def test_npc_time_events_count(self):
        te = _load_json("time_events.json")
        assert len(te["npc_time_events"]) == 8

    def test_npc_events_have_dialogue(self):
        te = _load_json("time_events.json")
        for evt in te["npc_time_events"]:
            assert "dialogue" in evt
            assert len(evt["dialogue"]) > 0

    def test_time_scale(self):
        te = _load_json("time_events.json")
        ts = te["time_scale"]
        assert ts["hours_per_day"] == 24
        assert ts["minutes_per_hour"] == 60


# ──── Battle Animations ──────────────────────────────────────

class TestBattleAnimations:
    def test_screen_shake_levels(self):
        ba = _load_json("battle_animations.json")
        shake = ba["screen_effects"]["screen_shake"]
        assert len(shake) == 3
        assert "intensity_light" in shake
        assert "intensity_heavy" in shake

    def test_screen_flash_types(self):
        ba = _load_json("battle_animations.json")
        assert len(ba["screen_effects"]["screen_flash"]) == 5

    def test_screen_tint_types(self):
        ba = _load_json("battle_animations.json")
        assert len(ba["screen_effects"]["screen_tint"]) == 5

    def test_flash_colors_valid(self):
        ba = _load_json("battle_animations.json")
        import re
        hex_pat = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for name, flash in ba["screen_effects"]["screen_flash"].items():
            assert hex_pat.match(flash["color"]), f"{name} bad color"

    def test_sprite_animation_count(self):
        ba = _load_json("battle_animations.json")
        assert len(ba["sprite_animations"]) == 8

    def test_sprite_anims_have_description(self):
        ba = _load_json("battle_animations.json")
        for name, anim in ba["sprite_animations"].items():
            assert "description" in anim, f"{name} missing description"

    def test_ui_animation_count(self):
        ba = _load_json("battle_animations.json")
        assert len(ba["ui_animations"]) == 6

    def test_hp_bar_thresholds(self):
        ba = _load_json("battle_animations.json")
        hp = ba["ui_animations"]["hp_bar"]
        thresholds = hp["color_thresholds"]
        assert "high" in thresholds
        assert "medium" in thresholds
        assert "low" in thresholds

    def test_transition_count(self):
        ba = _load_json("battle_animations.json")
        assert len(ba["transitions"]) == 4

    def test_transitions_have_type(self):
        ba = _load_json("battle_animations.json")
        for name, trans in ba["transitions"].items():
            assert "type" in trans, f"{name} missing type"
            assert "duration_ms" in trans, f"{name} missing duration_ms"

    def test_shake_intensity_ordering(self):
        ba = _load_json("battle_animations.json")
        shake = ba["screen_effects"]["screen_shake"]
        assert shake["intensity_light"]["offset_x"] < shake["intensity_heavy"]["offset_x"]

    def test_catch_shake_config(self):
        ba = _load_json("battle_animations.json")
        cs = ba["ui_animations"]["catch_shake"]
        assert cs["max_shakes"] == 3
        assert cs["sparkle_on_catch"] is True


# ──── Control Bindings ───────────────────────────────────────

class TestControlBindings:
    def test_binding_count(self):
        cb = _load_json("control_bindings.json")
        assert len(cb["default_bindings"]) == 18

    def test_bindings_have_primary(self):
        cb = _load_json("control_bindings.json")
        for action, binding in cb["default_bindings"].items():
            assert "primary" in binding, f"{action} missing primary"
            assert binding["primary"] is not None, f"{action} has null primary"

    def test_movement_bindings(self):
        cb = _load_json("control_bindings.json")
        bindings = cb["default_bindings"]
        assert bindings["move_up"]["secondary"] == "w"
        assert bindings["move_down"]["secondary"] == "s"
        assert bindings["move_left"]["secondary"] == "a"
        assert bindings["move_right"]["secondary"] == "d"

    def test_action_category_count(self):
        cb = _load_json("control_bindings.json")
        assert len(cb["action_categories"]) == 4

    def test_categories_reference_valid_actions(self):
        cb = _load_json("control_bindings.json")
        all_actions = set(cb["default_bindings"].keys())
        for cat, actions in cb["action_categories"].items():
            for action in actions:
                assert action in all_actions, \
                    f"Category {cat} references unknown action: {action}"

    def test_rebinding_rules(self):
        cb = _load_json("control_bindings.json")
        rules = cb["rebinding_rules"]
        assert rules["allow_rebind"] is True
        assert rules["max_bindings_per_action"] >= 1

    def test_gamepad_config(self):
        cb = _load_json("control_bindings.json")
        gp = cb["gamepad_config"]
        assert gp["enabled"] is True
        assert 0.0 < gp["deadzone"] < 1.0
        assert len(gp["button_map"]) == 10

    def test_touch_controls(self):
        cb = _load_json("control_bindings.json")
        tc = cb["touch_controls"]
        assert "enabled" in tc
        assert "dpad_position" in tc
        assert "action_buttons" in tc

    def test_input_settings(self):
        cb = _load_json("control_bindings.json")
        ins = cb["input_settings"]
        assert ins["key_repeat_delay_ms"] > 0
        assert ins["key_repeat_rate_ms"] > 0
        assert "diagonal_movement" in ins

    def test_no_diagonal_by_default(self):
        cb = _load_json("control_bindings.json")
        assert cb["input_settings"]["diagonal_movement"] is False


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
