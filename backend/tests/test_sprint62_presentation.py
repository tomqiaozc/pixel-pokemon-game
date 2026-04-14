"""Tests for Sprint 62: Credits sequence, name entry, title screen.

These tests verify credits roll configuration, character naming screens,
and title screen/intro sequence setup.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Credits Sequence ──────────────────────────────────────

class TestCreditsSequence:
    def test_section_count(self):
        cs = _load_json("credits_sequence.json")
        assert len(cs["sections"]) == 8

    def test_sections_have_fields(self):
        cs = _load_json("credits_sequence.json")
        for sec in cs["sections"]:
            assert "id" in sec
            assert "title" in sec
            assert "entries" in sec
            assert "display_ms" in sec
            assert len(sec["entries"]) >= 1

    def test_unique_section_ids(self):
        cs = _load_json("credits_sequence.json")
        ids = [s["id"] for s in cs["sections"]]
        assert len(ids) == len(set(ids))

    def test_credits_config(self):
        cs = _load_json("credits_sequence.json")
        c = cs["credits"]
        assert c["total_duration_ms"] > 0
        assert c["scroll_speed"] > 0

    def test_pokemon_parade(self):
        cs = _load_json("credits_sequence.json")
        pp = cs["pokemon_parade"]
        assert pp["enabled"] is True
        assert pp["pokemon_count"] > 0

    def test_scene_count(self):
        cs = _load_json("credits_sequence.json")
        assert len(cs["scenes"]) == 4

    def test_scenes_have_fields(self):
        cs = _load_json("credits_sequence.json")
        for scene in cs["scenes"]:
            assert "id" in scene
            assert "type" in scene
            assert "duration_ms" in scene

    def test_the_end_scene(self):
        cs = _load_json("credits_sequence.json")
        end = next(s for s in cs["scenes"] if s["id"] == "the_end")
        assert end["text"] == "THE END"

    def test_skip_config(self):
        cs = _load_json("credits_sequence.json")
        assert cs["skip_enabled"] is False
        assert cs["skip_after_first_view"] is True

    def test_end_action(self):
        cs = _load_json("credits_sequence.json")
        assert cs["end_action"] == "return_to_title"


# ──── Name Entry ────────────────────────────────────────────

class TestNameEntry:
    def test_player_name_config(self):
        ne = _load_json("name_entry.json")
        pn = ne["player_name"]
        assert pn["max_length"] == 7
        assert pn["min_length"] == 1

    def test_player_default_names(self):
        ne = _load_json("name_entry.json")
        defaults = ne["player_name"]["default_names"]
        assert len(defaults) == 4
        assert "RED" in defaults

    def test_rival_name_config(self):
        ne = _load_json("name_entry.json")
        rn = ne["rival_name"]
        assert rn["max_length"] == 7
        assert "BLUE" in rn["default_names"]

    def test_pokemon_nickname(self):
        ne = _load_json("name_entry.json")
        nn = ne["pokemon_nickname"]
        assert nn["max_length"] == 10
        assert nn["skip_option"] is True

    def test_keyboard_pages(self):
        ne = _load_json("name_entry.json")
        pages = ne["keyboard"]["pages"]
        assert len(pages) == 2

    def test_keyboard_buttons(self):
        ne = _load_json("name_entry.json")
        buttons = ne["keyboard"]["buttons"]
        assert len(buttons) == 3
        actions = {b["action"] for b in buttons}
        assert "confirm_name" in actions
        assert "delete_last" in actions

    def test_display_config(self):
        ne = _load_json("name_entry.json")
        d = ne["display"]
        assert d["screen_size"]["width"] == 240
        assert d["screen_size"]["height"] == 160
        assert d["cursor_blink_ms"] > 0

    def test_validation(self):
        ne = _load_json("name_entry.json")
        v = ne["validation"]
        assert v["trim_whitespace"] is True


# ──── Title Screen ──────────────────────────────────────────

class TestTitleScreen:
    def test_logo_config(self):
        ts = _load_json("title_screen.json")
        logo = ts["title_screen"]["logo"]
        assert logo["text"] == "Pixel Pokemon"
        assert logo["animation"] == "fade_in"

    def test_menu_option_count(self):
        ts = _load_json("title_screen.json")
        assert len(ts["menu_options"]) == 3

    def test_menu_options_have_fields(self):
        ts = _load_json("title_screen.json")
        for opt in ts["menu_options"]:
            assert "id" in opt
            assert "label" in opt

    def test_new_game_always_visible(self):
        ts = _load_json("title_screen.json")
        ng = next(o for o in ts["menu_options"] if o["id"] == "new_game")
        assert ng["always_visible"] is True

    def test_continue_conditional(self):
        ts = _load_json("title_screen.json")
        cont = next(o for o in ts["menu_options"] if o["id"] == "continue")
        assert cont["visible_if"] == "save_exists"

    def test_menu_config(self):
        ts = _load_json("title_screen.json")
        mc = ts["menu_config"]
        assert mc["cursor_blink_ms"] > 0

    def test_intro_sequence(self):
        ts = _load_json("title_screen.json")
        intro = ts["intro_sequence"]
        assert intro["enabled"] is True
        assert intro["skip_with_button"] is True

    def test_intro_scene_count(self):
        ts = _load_json("title_screen.json")
        assert len(ts["intro_sequence"]["scenes"]) == 4

    def test_professor_intro(self):
        ts = _load_json("title_screen.json")
        prof = next(s for s in ts["intro_sequence"]["scenes"]
                    if s["id"] == "professor_intro")
        assert prof["character"] == "Professor Oak"
        assert len(prof["lines"]) == 5

    def test_attract_mode(self):
        ts = _load_json("title_screen.json")
        am = ts["attract_mode"]
        assert am["enabled"] is True
        assert am["idle_timeout_ms"] > 0

    def test_pokemon_animation(self):
        ts = _load_json("title_screen.json")
        pa = ts["pokemon_animation"]
        assert pa["enabled"] is True
        assert pa["pokemon"] == "Nidorino"


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
