"""Tests for Sprint 54: Accessibility options, weather effects, achievement rewards.

These tests verify accessibility settings, weather visual effects,
and achievement reward data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Accessibility Options ──────────────────────────────────

class TestAccessibilityOptions:
    def test_colorblind_mode_count(self):
        ao = _load_json("accessibility_options.json")
        assert len(ao["colorblind_modes"]) == 4

    def test_colorblind_includes_none(self):
        ao = _load_json("accessibility_options.json")
        assert "none" in ao["colorblind_modes"]
        assert ao["colorblind_modes"]["none"]["filter"] is None

    def test_colorblind_modes_have_fields(self):
        ao = _load_json("accessibility_options.json")
        for name, mode in ao["colorblind_modes"].items():
            assert "display_name" in mode, f"{name} missing display_name"
            assert "description" in mode, f"{name} missing description"
            assert "filter" in mode, f"{name} missing filter"

    def test_screen_reader_config(self):
        ao = _load_json("accessibility_options.json")
        sr = ao["screen_reader"]
        assert "enabled" in sr
        assert sr["enabled"] is False
        assert "verbosity" in sr
        assert len(sr["verbosity_options"]) >= 3

    def test_font_scale_options(self):
        ao = _load_json("accessibility_options.json")
        scales = ao["font_settings"]["scale_options"]
        assert len(scales) == 5
        assert 1.0 in scales

    def test_visual_settings(self):
        ao = _load_json("accessibility_options.json")
        vs = ao["visual_settings"]
        assert "screen_shake_enabled" in vs
        assert "flash_effects_enabled" in vs
        assert "reduce_motion" in vs

    def test_cursor_size_options(self):
        ao = _load_json("accessibility_options.json")
        options = ao["visual_settings"]["cursor_size_options"]
        assert len(options) >= 3
        assert "normal" in options

    def test_audio_settings(self):
        ao = _load_json("accessibility_options.json")
        audio = ao["audio_settings"]
        assert "mono_audio" in audio
        assert "captions_enabled" in audio

    def test_input_accessibility(self):
        ao = _load_json("accessibility_options.json")
        inp = ao["input_settings"]
        assert "hold_instead_of_tap" in inp
        assert "auto_advance_text" in inp
        assert inp["auto_advance_delay_ms"] > 0

    def test_battle_accessibility(self):
        ao = _load_json("accessibility_options.json")
        ba = ao["battle_accessibility"]
        assert "extended_timer" in ba
        assert ba["timer_multiplier"] >= 1.0


# ──── Weather Effects ────────────────────────────────────────

class TestWeatherEffects:
    def test_weather_type_count(self):
        we = _load_json("weather_effects.json")
        assert len(we["weather_types"]) == 6

    def test_clear_weather_exists(self):
        we = _load_json("weather_effects.json")
        assert "clear" in we["weather_types"]

    def test_weather_have_overworld_effects(self):
        we = _load_json("weather_effects.json")
        for name, wt in we["weather_types"].items():
            assert "overworld_effects" in wt, f"{name} missing overworld_effects"
            assert "battle_effects" in wt, f"{name} missing battle_effects"

    def test_overworld_have_fields(self):
        we = _load_json("weather_effects.json")
        for name, wt in we["weather_types"].items():
            ow = wt["overworld_effects"]
            assert "overlay_opacity" in ow, f"{name} missing overlay_opacity"
            assert "brightness_modifier" in ow, f"{name} missing brightness_modifier"

    def test_rain_boosts_water(self):
        we = _load_json("weather_effects.json")
        rain = we["weather_types"]["rain"]["battle_effects"]
        assert rain["move_boost"]["type"] == "water"
        assert rain["move_boost"]["multiplier"] > 1.0

    def test_sun_boosts_fire(self):
        we = _load_json("weather_effects.json")
        sun = we["weather_types"]["sun"]["battle_effects"]
        assert sun["move_boost"]["type"] == "fire"
        assert sun["move_boost"]["multiplier"] > 1.0

    def test_sandstorm_damage(self):
        we = _load_json("weather_effects.json")
        ss = we["weather_types"]["sandstorm"]["battle_effects"]
        assert "damage_per_turn" in ss
        assert "rock" in ss["damage_per_turn"]["immune_types"]

    def test_battle_messages(self):
        we = _load_json("weather_effects.json")
        for name, wt in we["weather_types"].items():
            if name != "clear":
                be = wt["battle_effects"]
                assert be["start_message"] is not None, f"{name} missing start_message"

    def test_route_weather_count(self):
        we = _load_json("weather_effects.json")
        assert len(we["route_weather"]) == 11

    def test_route_weather_have_default(self):
        we = _load_json("weather_effects.json")
        for route, config in we["route_weather"].items():
            assert "default" in config, f"{route} missing default weather"

    def test_weather_transitions(self):
        we = _load_json("weather_effects.json")
        wt = we["weather_transitions"]
        assert wt["fade_duration_ms"] > 0
        assert wt["particle_fade_in_ms"] > 0


# ──── Achievement Rewards ────────────────────────────────────

class TestAchievementRewards:
    def test_reward_count(self):
        ar = _load_json("achievement_rewards.json")
        assert len(ar["rewards"]) == 32

    def test_all_match_achievements(self):
        ar = _load_json("achievement_rewards.json")
        ach = _load_json("achievements.json")
        ach_ids = {a["id"] for a in ach}
        for reward_key, reward in ar["rewards"].items():
            assert reward["achievement_id"] in ach_ids, \
                f"Reward {reward_key} references unknown achievement {reward['achievement_id']}"

    def test_all_achievements_have_rewards(self):
        ar = _load_json("achievement_rewards.json")
        ach = _load_json("achievements.json")
        reward_ids = {r["achievement_id"] for r in ar["rewards"].values()}
        for a in ach:
            assert a["id"] in reward_ids, f"Achievement {a['id']} has no reward"

    def test_rewards_have_type(self):
        ar = _load_json("achievement_rewards.json")
        valid_types = set(ar["reward_types"])
        for key, reward in ar["rewards"].items():
            assert reward["reward_type"] in valid_types, \
                f"{key} invalid type: {reward['reward_type']}"

    def test_rewards_have_notification(self):
        ar = _load_json("achievement_rewards.json")
        for key, reward in ar["rewards"].items():
            assert "notification" in reward, f"{key} missing notification"
            assert len(reward["notification"]) > 0

    def test_item_rewards_have_item(self):
        ar = _load_json("achievement_rewards.json")
        for key, reward in ar["rewards"].items():
            if reward["reward_type"] == "item":
                assert "reward_item" in reward, f"{key} missing reward_item"
                assert "reward_quantity" in reward, f"{key} missing reward_quantity"
                assert reward["reward_quantity"] > 0

    def test_money_rewards_have_amount(self):
        ar = _load_json("achievement_rewards.json")
        for key, reward in ar["rewards"].items():
            if reward["reward_type"] == "money":
                assert "reward_amount" in reward, f"{key} missing reward_amount"
                assert reward["reward_amount"] > 0

    def test_champion_reward(self):
        ar = _load_json("achievement_rewards.json")
        champ = ar["rewards"]["become_champion"]
        assert champ["reward_type"] == "title"
        assert champ["reward_title"] == "Champion"

    def test_display_settings(self):
        ar = _load_json("achievement_rewards.json")
        ds = ar["display_settings"]
        assert ds["show_popup"] is True
        assert ds["popup_duration_ms"] > 0
        assert ds["play_fanfare"] is True

    def test_reward_types(self):
        ar = _load_json("achievement_rewards.json")
        assert len(ar["reward_types"]) == 4


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
