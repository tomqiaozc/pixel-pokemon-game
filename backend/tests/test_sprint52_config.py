"""Tests for Sprint 52: Sound effects, minimap data, difficulty settings.

These tests verify sound effect definitions, minimap region layout,
and difficulty scaling configuration.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Sound Effects ──────────────────────────────────────────

class TestSoundEffects:
    def test_category_count(self):
        se = _load_json("sound_effects.json")
        assert len(se["categories"]) == 3

    def test_ui_sfx_count(self):
        se = _load_json("sound_effects.json")
        assert len(se["categories"]["ui"]) == 15

    def test_battle_sfx_count(self):
        se = _load_json("sound_effects.json")
        assert len(se["categories"]["battle"]) == 37

    def test_environment_sfx_count(self):
        se = _load_json("sound_effects.json")
        assert len(se["categories"]["environment"]) == 16

    def test_all_have_required_fields(self):
        se = _load_json("sound_effects.json")
        for cat_name, cat in se["categories"].items():
            for sfx_name, sfx in cat.items():
                assert "file" in sfx, f"{cat_name}/{sfx_name} missing file"
                assert "volume" in sfx, f"{cat_name}/{sfx_name} missing volume"
                assert "priority" in sfx, f"{cat_name}/{sfx_name} missing priority"

    def test_volumes_in_range(self):
        se = _load_json("sound_effects.json")
        for cat_name, cat in se["categories"].items():
            for sfx_name, sfx in cat.items():
                assert 0.0 <= sfx["volume"] <= 1.0, \
                    f"{cat_name}/{sfx_name} volume {sfx['volume']} out of range"

    def test_valid_priorities(self):
        se = _load_json("sound_effects.json")
        valid = {"low", "medium", "high"}
        for cat_name, cat in se["categories"].items():
            for sfx_name, sfx in cat.items():
                assert sfx["priority"] in valid, \
                    f"{cat_name}/{sfx_name} invalid priority: {sfx['priority']}"

    def test_files_have_extension(self):
        se = _load_json("sound_effects.json")
        for cat_name, cat in se["categories"].items():
            for sfx_name, sfx in cat.items():
                assert sfx["file"].endswith(".ogg"), \
                    f"{cat_name}/{sfx_name} file not .ogg: {sfx['file']}"

    def test_volume_settings(self):
        se = _load_json("sound_effects.json")
        vs = se["volume_settings"]
        assert "master" in vs
        assert "sfx" in vs
        assert "music" in vs
        for key, setting in vs.items():
            assert setting["min"] == 0.0
            assert setting["max"] == 1.0

    def test_max_concurrent_sfx(self):
        se = _load_json("sound_effects.json")
        assert se["max_concurrent_sfx"] >= 2

    def test_battle_start_exists(self):
        se = _load_json("sound_effects.json")
        assert "battle_start" in se["categories"]["battle"]

    def test_pokeball_sounds(self):
        se = _load_json("sound_effects.json")
        battle = se["categories"]["battle"]
        assert "pokeball_throw" in battle
        assert "pokeball_catch" in battle
        assert "pokeball_break" in battle


# ──── Minimap Data ───────────────────────────────────────────

class TestMinimapData:
    def test_location_count(self):
        md = _load_json("minimap_data.json")
        assert len(md["locations"]) == 41

    def test_tile_color_count(self):
        md = _load_json("minimap_data.json")
        assert len(md["tile_colors"]) == 13

    def test_settings_present(self):
        md = _load_json("minimap_data.json")
        ms = md["minimap_settings"]
        assert "position" in ms
        assert "size" in ms
        assert "opacity" in ms
        assert "toggle_key" in ms

    def test_region_bounds(self):
        md = _load_json("minimap_data.json")
        rb = md["region_bounds"]
        assert rb["x_min"] < rb["x_max"]
        assert rb["y_min"] < rb["y_max"]

    def test_locations_have_fields(self):
        md = _load_json("minimap_data.json")
        for loc_id, loc in md["locations"].items():
            assert "display_name" in loc, f"{loc_id} missing display_name"
            assert "minimap_x" in loc, f"{loc_id} missing minimap_x"
            assert "minimap_y" in loc, f"{loc_id} missing minimap_y"
            assert "type" in loc, f"{loc_id} missing type"
            assert "connections" in loc, f"{loc_id} missing connections"

    def test_location_types_valid(self):
        md = _load_json("minimap_data.json")
        valid_types = set(md["tile_colors"].keys())
        for loc_id, loc in md["locations"].items():
            assert loc["type"] in valid_types, \
                f"{loc_id} type '{loc['type']}' not in tile_colors"

    def test_pallet_town_present(self):
        md = _load_json("minimap_data.json")
        assert "pallet_town" in md["locations"]
        assert md["locations"]["pallet_town"]["type"] == "town"

    def test_indigo_plateau_present(self):
        md = _load_json("minimap_data.json")
        assert "indigo_plateau" in md["locations"]
        assert md["locations"]["indigo_plateau"]["type"] == "elite_four"

    def test_connections_reference_valid_locations(self):
        md = _load_json("minimap_data.json")
        all_ids = set(md["locations"].keys())
        for loc_id, loc in md["locations"].items():
            for conn in loc["connections"]:
                assert conn in all_ids, \
                    f"{loc_id} connects to unknown location: {conn}"

    def test_tile_colors_are_hex(self):
        md = _load_json("minimap_data.json")
        import re
        hex_pat = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for name, color in md["tile_colors"].items():
            assert hex_pat.match(color), f"{name} bad color: {color}"

    def test_zoom_levels(self):
        md = _load_json("minimap_data.json")
        zl = md["minimap_settings"]["zoom_levels"]
        assert len(zl) >= 2
        assert zl == sorted(zl)


# ──── Difficulty Settings ────────────────────────────────────

class TestDifficultySettings:
    def test_mode_count(self):
        ds = _load_json("difficulty_settings.json")
        assert len(ds["difficulty_modes"]) == 4

    def test_default_normal(self):
        ds = _load_json("difficulty_settings.json")
        assert ds["current_difficulty"] == "normal"

    def test_modes_have_fields(self):
        ds = _load_json("difficulty_settings.json")
        required = ["display_name", "description", "exp_multiplier",
                     "money_multiplier", "catch_rate_modifier", "ai_difficulty"]
        for mode_name, mode in ds["difficulty_modes"].items():
            for field in required:
                assert field in mode, f"{mode_name} missing {field}"

    def test_exp_multiplier_ordering(self):
        ds = _load_json("difficulty_settings.json")
        modes = ds["difficulty_modes"]
        assert modes["easy"]["exp_multiplier"] > modes["normal"]["exp_multiplier"]
        assert modes["normal"]["exp_multiplier"] > modes["hard"]["exp_multiplier"]

    def test_nuzlocke_special_rules(self):
        ds = _load_json("difficulty_settings.json")
        nuz = ds["difficulty_modes"]["nuzlocke"]
        assert "special_rules" in nuz
        assert nuz["special_rules"]["perma_faint"] is True
        assert nuz["special_rules"]["first_encounter_only"] is True

    def test_ai_levels(self):
        ds = _load_json("difficulty_settings.json")
        ai = ds["ai_difficulty_levels"]
        assert len(ai) == 3
        assert "basic" in ai
        assert "standard" in ai
        assert "smart" in ai

    def test_ai_fields(self):
        ds = _load_json("difficulty_settings.json")
        for level_name, level in ds["ai_difficulty_levels"].items():
            assert "description" in level
            assert "use_type_advantage" in level

    def test_smart_ai_uses_items(self):
        ds = _load_json("difficulty_settings.json")
        assert ds["ai_difficulty_levels"]["smart"]["use_items"] is True

    def test_basic_ai_no_type_advantage(self):
        ds = _load_json("difficulty_settings.json")
        assert ds["ai_difficulty_levels"]["basic"]["use_type_advantage"] is False

    def test_level_scaling_config(self):
        ds = _load_json("difficulty_settings.json")
        ls = ds["level_scaling"]
        assert "enabled" in ls
        assert "method" in ls
        assert len(ls["level_caps"]) >= 8

    def test_battle_style_options(self):
        ds = _load_json("difficulty_settings.json")
        bs = ds["battle_style"]
        assert "shift" in bs["options"]
        assert "set" in bs["options"]


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
