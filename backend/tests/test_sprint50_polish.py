"""Tests for Sprint 50: Item visuals, credits, localization config.

These tests verify item display properties, credits/ending sequence,
and localization/text system configuration.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Item Visuals ────────────────────────────────────────────

class TestItemVisuals:
    def test_visual_count(self):
        iv = _load_json("item_visuals.json")
        assert len(iv) == 93

    def test_all_have_fields(self):
        iv = _load_json("item_visuals.json")
        for name, data in iv.items():
            assert "sprite_id" in data, f"{name} missing sprite_id"
            assert "category_color" in data, f"{name} missing category_color"
            assert "rarity" in data, f"{name} missing rarity"
            assert "stackable" in data, f"{name} missing stackable"

    def test_colors_are_hex(self):
        iv = _load_json("item_visuals.json")
        import re
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for name, data in iv.items():
            assert hex_pattern.match(data["category_color"]), \
                f"{name} color {data['category_color']} is not valid hex"

    VALID_RARITIES = {"common", "uncommon", "rare", "unique"}

    def test_rarities_valid(self):
        iv = _load_json("item_visuals.json")
        for name, data in iv.items():
            assert data["rarity"] in self.VALID_RARITIES, \
                f"{name} has invalid rarity: {data['rarity']}"

    def test_items_match_items_json(self):
        iv = _load_json("item_visuals.json")
        items = _load_json("items.json")
        item_names = {i["name"] for i in items}
        for visual_name in iv:
            assert visual_name in item_names, \
                f"{visual_name} not in items.json"

    def test_sprite_ids_unique(self):
        iv = _load_json("item_visuals.json")
        sprite_ids = [d["sprite_id"] for d in iv.values()]
        assert len(sprite_ids) == len(set(sprite_ids))

    def test_potion_common(self):
        iv = _load_json("item_visuals.json")
        assert iv["Potion"]["rarity"] == "common"

    def test_master_ball_visual(self):
        iv = _load_json("item_visuals.json")
        assert "Master Ball" in iv


# ──── Credits Data ────────────────────────────────────────────

class TestCreditsData:
    def test_trigger(self):
        cd = _load_json("credits_data.json")
        assert cd["trigger"] == "champion_defeated"

    def test_sequence_count(self):
        cd = _load_json("credits_data.json")
        assert len(cd["sequence"]) >= 4

    def test_sequence_types(self):
        cd = _load_json("credits_data.json")
        types = {s["type"] for s in cd["sequence"]}
        assert "hall_of_fame" in types
        assert "credits_roll" in types
        assert "the_end" in types

    def test_hall_of_fame_shows_team(self):
        cd = _load_json("credits_data.json")
        hof = next(s for s in cd["sequence"] if s["type"] == "hall_of_fame")
        assert hof["shows_team"] is True

    def test_credits_has_background_scenes(self):
        cd = _load_json("credits_data.json")
        credits = next(s for s in cd["sequence"] if s["type"] == "credits_roll")
        assert len(credits["background_scenes"]) >= 5

    def test_staff_list(self):
        cd = _load_json("credits_data.json")
        staff = cd["staff"]
        assert len(staff) >= 10
        for member in staff:
            assert "role" in member
            assert "name" in member

    def test_post_credits_unlocks(self):
        cd = _load_json("credits_data.json")
        pc = cd["post_credits"]
        assert len(pc["unlocks"]) >= 4
        assert pc["return_to"] == "pallet_town"

    def test_total_duration(self):
        cd = _load_json("credits_data.json")
        assert cd["total_duration_seconds"] > 0

    def test_the_end_shows_stats(self):
        cd = _load_json("credits_data.json")
        end = next(s for s in cd["sequence"] if s["type"] == "the_end")
        assert end["shows_play_time"] is True
        assert end["shows_pokedex_count"] is True


# ──── Localization Config ─────────────────────────────────────

class TestLocalizationConfig:
    def test_default_language(self):
        lc = _load_json("localization_config.json")
        assert lc["default_language"] == "en"

    def test_supported_languages(self):
        lc = _load_json("localization_config.json")
        langs = lc["supported_languages"]
        assert len(langs) >= 8
        codes = {l["code"] for l in langs}
        assert "en" in codes
        assert "ja" in codes

    def test_languages_have_fields(self):
        lc = _load_json("localization_config.json")
        for lang in lc["supported_languages"]:
            assert "code" in lang
            assert "name" in lang
            assert "native_name" in lang
            assert "direction" in lang

    def test_text_categories(self):
        lc = _load_json("localization_config.json")
        cats = lc["text_categories"]
        assert len(cats) >= 10
        assert "ui" in cats
        assert "dialogue" in cats
        assert "battle" in cats
        assert "pokemon_names" in cats

    def test_text_speed_options(self):
        lc = _load_json("localization_config.json")
        speeds = lc["text_speed_options"]
        assert len(speeds) >= 4
        assert speeds["slow"]["chars_per_second"] < speeds["fast"]["chars_per_second"]

    def test_font_config(self):
        lc = _load_json("localization_config.json")
        font = lc["font_config"]
        assert font["font_size"] > 0
        assert font["max_line_width_chars"] > 0
        assert font["name_max_length"] == 10

    def test_string_formatting(self):
        lc = _load_json("localization_config.json")
        fmt = lc["string_formatting"]
        assert "{PLAYER}" in fmt["player_name_placeholder"]
        assert "{RIVAL}" in fmt["rival_name_placeholder"]
        assert "{POKEMON}" in fmt["pokemon_name_placeholder"]

    def test_fallback_strategy(self):
        lc = _load_json("localization_config.json")
        assert lc["fallback_strategy"] == "use_default_language"

    def test_pluralization_rules(self):
        lc = _load_json("localization_config.json")
        plural = lc["pluralization"]
        assert "en" in plural
        assert "ja" in plural


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
