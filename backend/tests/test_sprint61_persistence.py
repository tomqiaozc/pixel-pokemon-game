"""Tests for Sprint 61: Save system, Pokemon storage, Hall of Fame.

These tests verify save file configuration, PC box storage system,
and Hall of Fame champion records.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Save System ───────────────────────────────────────────

class TestSaveSystem:
    def test_quick_save(self):
        ss = _load_json("save_system.json")
        qs = ss["quick_save"]
        assert qs["enabled"] is True
        assert qs["hotkey"] == "F5"

    def test_section_count(self):
        ss = _load_json("save_system.json")
        assert len(ss["save_data_structure"]["sections"]) == 10

    def test_sections_have_fields(self):
        ss = _load_json("save_system.json")
        for sec in ss["save_data_structure"]["sections"]:
            assert "id" in sec
            assert "description" in sec
            assert "compressed" in sec

    def test_unique_section_ids(self):
        ss = _load_json("save_system.json")
        ids = [s["id"] for s in ss["save_data_structure"]["sections"]]
        assert len(ids) == len(set(ids))

    def test_save_screen_config(self):
        ss = _load_json("save_system.json")
        sc = ss["save_screen"]
        assert sc["confirm_overwrite"] is True
        assert sc["save_animation_ms"] > 0

    def test_save_screen_messages(self):
        ss = _load_json("save_system.json")
        sc = ss["save_screen"]
        assert len(sc["saving_message"]) > 0
        assert len(sc["save_complete_message"]) > 0

    def test_file_config(self):
        ss = _load_json("save_system.json")
        fc = ss["file_config"]
        assert fc["format"] == "json"
        assert fc["extension"] == ".sav"

    def test_preview_fields(self):
        ss = _load_json("save_system.json")
        pf = ss["save_screen"]["preview_fields"]
        assert len(pf) == 5
        assert "player_name" in pf


# ──── Pokemon Storage ──────────────────────────────────────

class TestPokemonStorage:
    def test_box_count(self):
        ps = _load_json("pokemon_storage.json")
        assert ps["box_config"]["total_boxes"] == 12

    def test_pokemon_per_box(self):
        ps = _load_json("pokemon_storage.json")
        assert ps["box_config"]["pokemon_per_box"] == 30

    def test_total_capacity(self):
        ps = _load_json("pokemon_storage.json")
        bc = ps["box_config"]
        assert bc["total_capacity"] == bc["total_boxes"] * bc["pokemon_per_box"]

    def test_box_list_count(self):
        ps = _load_json("pokemon_storage.json")
        assert len(ps["boxes"]) == 12

    def test_boxes_have_fields(self):
        ps = _load_json("pokemon_storage.json")
        for box in ps["boxes"]:
            assert "id" in box
            assert "default_name" in box
            assert "default_wallpaper" in box

    def test_wallpaper_count(self):
        ps = _load_json("pokemon_storage.json")
        assert len(ps["wallpapers"]) == 12

    def test_wallpapers_have_fields(self):
        ps = _load_json("pokemon_storage.json")
        for wp in ps["wallpapers"]:
            assert "id" in wp
            assert "display_name" in wp
            assert "bg_color" in wp
            assert "unlocked" in wp

    def test_box_wallpapers_valid(self):
        ps = _load_json("pokemon_storage.json")
        wp_ids = {w["id"] for w in ps["wallpapers"]}
        for box in ps["boxes"]:
            assert box["default_wallpaper"] in wp_ids, \
                f"Box {box['id']} has invalid wallpaper: {box['default_wallpaper']}"

    def test_operation_count(self):
        ps = _load_json("pokemon_storage.json")
        assert len(ps["operations"]) == 6

    def test_restrictions(self):
        ps = _load_json("pokemon_storage.json")
        r = ps["restrictions"]
        assert r["min_party_size"] == 1
        assert r["cannot_deposit_last_pokemon"] is True
        assert r["release_confirm_required"] is True

    def test_sorting_options(self):
        ps = _load_json("pokemon_storage.json")
        assert len(ps["sorting_options"]) == 5

    def test_ui_config(self):
        ps = _load_json("pokemon_storage.json")
        ui = ps["ui_config"]
        assert ui["box_view_columns"] * ui["box_view_rows"] == 30

    def test_access_locations(self):
        ps = _load_json("pokemon_storage.json")
        assert len(ps["access_locations"]) == 2


# ──── Hall of Fame ─────────────────────────────────────────

class TestHallOfFame:
    def test_max_records(self):
        hof = _load_json("hall_of_fame.json")
        assert hof["hall_of_fame"]["max_records"] == 30

    def test_location(self):
        hof = _load_json("hall_of_fame.json")
        assert hof["hall_of_fame"]["location"] == "indigo_plateau"

    def test_record_fields(self):
        hof = _load_json("hall_of_fame.json")
        fields = hof["record_structure"]["fields"]
        assert len(fields) == 4
        field_ids = {f["id"] for f in fields}
        assert "record_number" in field_ids
        assert "team" in field_ids

    def test_team_member_fields(self):
        hof = _load_json("hall_of_fame.json")
        tmf = hof["record_structure"]["team_member_fields"]
        assert len(tmf) == 6
        ids = {f["id"] for f in tmf}
        assert "species" in ids
        assert "level" in ids

    def test_display_config(self):
        hof = _load_json("hall_of_fame.json")
        d = hof["display"]
        assert d["screen_size"]["width"] == 240
        assert d["screen_size"]["height"] == 160
        assert d["show_sprite"] is True

    def test_ceremony_enabled(self):
        hof = _load_json("hall_of_fame.json")
        c = hof["ceremony"]
        assert c["enabled"] is True
        assert c["credits_after"] is True
        assert c["sparkle_effect"] is True

    def test_ceremony_return(self):
        hof = _load_json("hall_of_fame.json")
        assert hof["ceremony"]["return_to"] == "players_room"

    def test_viewing_config(self):
        hof = _load_json("hall_of_fame.json")
        v = hof["viewing"]
        assert v["browse_records"] is True
        assert v["newest_first"] is True

    def test_first_victory_rewards(self):
        hof = _load_json("hall_of_fame.json")
        rewards = hof["first_victory_rewards"]
        assert len(rewards) == 4

    def test_rewards_have_fields(self):
        hof = _load_json("hall_of_fame.json")
        for r in hof["first_victory_rewards"]:
            assert "type" in r
            assert "value" in r
            assert "description" in r


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
