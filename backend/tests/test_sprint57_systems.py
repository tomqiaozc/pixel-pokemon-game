"""Tests for Sprint 57: Menu screens, event flags, palette data.

These tests verify menu configurations, event flag system,
and color palette definitions.
"""
import json
import os
import re
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


HEX_PAT = re.compile(r"^#[0-9A-Fa-f]{6,8}$")


# ──── Menu Screens ───────────────────────────────────────────

class TestMenuScreens:
    def test_title_screen_options(self):
        ms = _load_json("menu_screens.json")
        assert len(ms["title_screen"]["options"]) == 3

    def test_pause_menu_options(self):
        ms = _load_json("menu_screens.json")
        assert len(ms["pause_menu"]["options"]) == 7

    def test_pause_options_have_fields(self):
        ms = _load_json("menu_screens.json")
        for opt in ms["pause_menu"]["options"]:
            assert "id" in opt
            assert "label" in opt
            assert "action" in opt

    def test_options_menu_sections(self):
        ms = _load_json("menu_screens.json")
        assert len(ms["options_menu"]["sections"]) == 6

    def test_options_have_type(self):
        ms = _load_json("menu_screens.json")
        valid_types = {"cycle", "slider", "button"}
        for section in ms["options_menu"]["sections"]:
            assert section["type"] in valid_types, \
                f"{section['id']} invalid type: {section['type']}"

    def test_bag_pockets(self):
        ms = _load_json("menu_screens.json")
        assert len(ms["bag_menu"]["pockets"]) == 4

    def test_party_menu_config(self):
        ms = _load_json("menu_screens.json")
        pm = ms["party_menu"]
        assert pm["max_party_size"] == 6
        assert pm["show_hp_bar"] is True

    def test_confirmation_dialog(self):
        ms = _load_json("menu_screens.json")
        cd = ms["confirmation_dialog"]
        assert "YES" in cd["options"]
        assert "NO" in cd["options"]

    def test_pause_menu_has_save(self):
        ms = _load_json("menu_screens.json")
        ids = [o["id"] for o in ms["pause_menu"]["options"]]
        assert "save" in ids

    def test_title_has_new_game(self):
        ms = _load_json("menu_screens.json")
        ids = [o["id"] for o in ms["title_screen"]["options"]]
        assert "new_game" in ids


# ──── Event Flags ────────────────────────────────────────────

class TestEventFlags:
    def test_category_count(self):
        ef = _load_json("event_flags.json")
        assert len(ef["categories"]) == 6

    def test_total_flag_count(self):
        ef = _load_json("event_flags.json")
        total = sum(len(cat["flags"]) for cat in ef["categories"].values())
        assert total == 54

    def test_flags_have_fields(self):
        ef = _load_json("event_flags.json")
        for cat_name, cat in ef["categories"].items():
            for flag in cat["flags"]:
                assert "id" in flag, f"Missing id in {cat_name}"
                assert "default" in flag, f"Missing default in {flag.get('id', '?')}"
                assert "description" in flag, f"Missing description in {flag.get('id', '?')}"

    def test_flags_default_false(self):
        ef = _load_json("event_flags.json")
        for cat_name, cat in ef["categories"].items():
            for flag in cat["flags"]:
                assert flag["default"] is False, \
                    f"{flag['id']} has non-false default"

    def test_unique_flag_ids(self):
        ef = _load_json("event_flags.json")
        all_ids = []
        for cat in ef["categories"].values():
            for flag in cat["flags"]:
                all_ids.append(flag["id"])
        assert len(all_ids) == len(set(all_ids))

    def test_gym_flags_count(self):
        ef = _load_json("event_flags.json")
        assert len(ef["categories"]["gyms"]["flags"]) == 8

    def test_tutorial_flags_match(self):
        ef = _load_json("event_flags.json")
        ts = _load_json("tutorial_system.json")
        tutorial_flags = {f["id"] for f in ef["categories"]["tutorials"]["flags"]}
        for tutorial in ts:
            assert tutorial["completed_flag"] in tutorial_flags, \
                f"Tutorial {tutorial['id']} flag {tutorial['completed_flag']} not in event_flags"

    def test_story_has_champion(self):
        ef = _load_json("event_flags.json")
        story_ids = {f["id"] for f in ef["categories"]["story"]["flags"]}
        assert "champion_defeated" in story_ids

    def test_hm_flags(self):
        ef = _load_json("event_flags.json")
        assert len(ef["categories"]["hms"]["flags"]) == 5

    def test_flag_count_summary(self):
        ef = _load_json("event_flags.json")
        for cat_name, expected in ef["flag_count_by_category"].items():
            actual = len(ef["categories"][cat_name]["flags"])
            assert actual == expected, \
                f"{cat_name}: expected {expected}, got {actual}"


# ──── Palette Data ───────────────────────────────────────────

class TestPaletteData:
    def test_type_palette_count(self):
        pd = _load_json("palette_data.json")
        assert len(pd["type_palettes"]) == 15

    def test_type_palettes_have_colors(self):
        pd = _load_json("palette_data.json")
        for type_name, palette in pd["type_palettes"].items():
            assert "primary" in palette, f"{type_name} missing primary"
            assert "secondary" in palette, f"{type_name} missing secondary"
            assert "dark" in palette, f"{type_name} missing dark"
            assert HEX_PAT.match(palette["primary"]), f"{type_name} bad primary"

    def test_ui_palette_count(self):
        pd = _load_json("palette_data.json")
        assert len(pd["ui_palette"]) == 17

    def test_ui_colors_valid(self):
        pd = _load_json("palette_data.json")
        for name, color in pd["ui_palette"].items():
            assert HEX_PAT.match(color), f"UI {name}: {color} invalid"

    def test_battle_palette_count(self):
        pd = _load_json("palette_data.json")
        assert len(pd["battle_palette"]) == 13

    def test_overworld_palette_count(self):
        pd = _load_json("palette_data.json")
        assert len(pd["overworld_palette"]) == 15

    def test_day_night_tint_count(self):
        pd = _load_json("palette_data.json")
        assert len(pd["day_night_tints"]) == 5

    def test_day_night_have_fields(self):
        pd = _load_json("palette_data.json")
        for name, tint in pd["day_night_tints"].items():
            assert "multiply_color" in tint, f"{name} missing multiply_color"
            assert "opacity" in tint, f"{name} missing opacity"

    def test_shiny_config(self):
        pd = _load_json("palette_data.json")
        sh = pd["shiny_hue_shift"]
        assert sh["method"] == "hue_rotate"
        assert sh["default_degrees"] > 0

    def test_hp_colors_in_ui(self):
        pd = _load_json("palette_data.json")
        ui = pd["ui_palette"]
        assert "hp_high" in ui
        assert "hp_medium" in ui
        assert "hp_low" in ui

    def test_status_colors_in_battle(self):
        pd = _load_json("palette_data.json")
        bp = pd["battle_palette"]
        assert "status_poison" in bp
        assert "status_burn" in bp
        assert "status_paralyze" in bp


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
