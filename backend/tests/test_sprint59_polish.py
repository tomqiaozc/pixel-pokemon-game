"""Tests for Sprint 59: Camera system, item effects, music jukebox.

These tests verify camera/viewport config, item use effects,
and music jukebox system.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Camera System ──────────────────────────────────────────

class TestCameraSystem:
    def test_viewport_dimensions(self):
        cs = _load_json("camera_system.json")
        vp = cs["viewport"]
        assert vp["width"] == 240
        assert vp["height"] == 160
        assert vp["tile_size"] == 16

    def test_follow_settings(self):
        cs = _load_json("camera_system.json")
        fs = cs["follow_settings"]
        assert fs["target"] == "player"
        assert fs["smoothing"] is True

    def test_dead_zone(self):
        cs = _load_json("camera_system.json")
        dz = cs["follow_settings"]["dead_zone"]
        assert dz["x"] > 0
        assert dz["y"] > 0

    def test_look_ahead(self):
        cs = _load_json("camera_system.json")
        la = cs["follow_settings"]["look_ahead"]
        assert la["enabled"] is True
        assert la["distance_tiles"] > 0

    def test_bounds_config(self):
        cs = _load_json("camera_system.json")
        assert cs["bounds"]["clamp_to_map"] is True

    def test_shake_effect(self):
        cs = _load_json("camera_system.json")
        shake = cs["effects"]["shake"]
        assert shake["enabled"] is True
        assert shake["max_offset"] > 0

    def test_cutscene_camera(self):
        cs = _load_json("camera_system.json")
        cc = cs["cutscene_camera"]
        assert cc["enabled"] is True
        assert cc["auto_return"] is True

    def test_letterbox(self):
        cs = _load_json("camera_system.json")
        lb = cs["cutscene_camera"]["letterbox"]
        assert lb["enabled"] is True
        assert lb["bar_height"] > 0

    def test_indoor_settings(self):
        cs = _load_json("camera_system.json")
        ind = cs["indoor_settings"]
        assert ind["center_on_room"] is True


# ──── Item Effects ───────────────────────────────────────────

class TestItemEffects:
    def test_battle_item_count(self):
        ie = _load_json("item_effects.json")
        assert len(ie["battle_items"]) == 29

    def test_field_item_count(self):
        ie = _load_json("item_effects.json")
        assert len(ie["field_items"]) == 13

    def test_battle_items_have_fields(self):
        ie = _load_json("item_effects.json")
        for name, item in ie["battle_items"].items():
            assert "effect" in item, f"{name} missing effect"
            assert "target" in item, f"{name} missing target"
            assert "message" in item, f"{name} missing message"

    def test_field_items_have_fields(self):
        ie = _load_json("item_effects.json")
        for name, item in ie["field_items"].items():
            assert "effect" in item, f"{name} missing effect"
            assert "message" in item, f"{name} missing message"

    def test_potion_heals_20(self):
        ie = _load_json("item_effects.json")
        assert ie["battle_items"]["Potion"]["effect"] == "heal_hp"
        assert ie["battle_items"]["Potion"]["value"] == 20

    def test_master_ball_catch_rate(self):
        ie = _load_json("item_effects.json")
        mb = ie["battle_items"]["Master Ball"]
        assert mb["catch_rate_modifier"] == 255

    def test_repel_items(self):
        ie = _load_json("item_effects.json")
        fi = ie["field_items"]
        assert fi["Repel"]["steps"] < fi["Super Repel"]["steps"]
        assert fi["Super Repel"]["steps"] < fi["Max Repel"]["steps"]

    def test_effect_types_defined(self):
        ie = _load_json("item_effects.json")
        assert len(ie["effect_types"]) == 25

    def test_effects_reference_valid_types(self):
        ie = _load_json("item_effects.json")
        valid_types = set(ie["effect_types"])
        for name, item in ie["battle_items"].items():
            assert item["effect"] in valid_types, \
                f"{name} invalid effect: {item['effect']}"
        for name, item in ie["field_items"].items():
            assert item["effect"] in valid_types, \
                f"{name} invalid effect: {item['effect']}"

    def test_revive_targets_fainted(self):
        ie = _load_json("item_effects.json")
        assert ie["battle_items"]["Revive"]["target"] == "fainted_pokemon"

    def test_stat_boost_items(self):
        ie = _load_json("item_effects.json")
        x_attack = ie["battle_items"]["X Attack"]
        assert x_attack["effect"] == "stat_boost"
        assert x_attack["stages"] >= 1


# ──── Music Jukebox ──────────────────────────────────────────

class TestMusicJukebox:
    def test_track_count(self):
        mj = _load_json("music_jukebox.json")
        assert len(mj["tracks"]) == 32

    def test_category_count(self):
        mj = _load_json("music_jukebox.json")
        assert len(mj["categories"]) == 7

    def test_tracks_have_fields(self):
        mj = _load_json("music_jukebox.json")
        for track in mj["tracks"]:
            assert "id" in track
            assert "name" in track
            assert "category" in track
            assert "duration_seconds" in track
            assert "unlocked_by_default" in track

    def test_tracks_valid_categories(self):
        mj = _load_json("music_jukebox.json")
        valid = set(mj["categories"])
        for track in mj["tracks"]:
            assert track["category"] in valid, \
                f"{track['id']} invalid category: {track['category']}"

    def test_unique_track_ids(self):
        mj = _load_json("music_jukebox.json")
        ids = [t["id"] for t in mj["tracks"]]
        assert len(ids) == len(set(ids))

    def test_default_unlocked_count(self):
        mj = _load_json("music_jukebox.json")
        unlocked = [t for t in mj["tracks"] if t["unlocked_by_default"]]
        assert len(unlocked) == 7

    def test_jukebox_config(self):
        mj = _load_json("music_jukebox.json")
        jb = mj["jukebox"]
        assert jb["enabled"] is True
        assert jb["unlock_requirement"] == "become_champion"

    def test_playback_settings(self):
        mj = _load_json("music_jukebox.json")
        ps = mj["playback_settings"]
        assert ps["crossfade_ms"] > 0
        assert ps["loop_by_default"] is True

    def test_durations_positive(self):
        mj = _load_json("music_jukebox.json")
        for track in mj["tracks"]:
            assert track["duration_seconds"] > 0, \
                f"{track['id']} non-positive duration"

    def test_battle_tracks_exist(self):
        mj = _load_json("music_jukebox.json")
        battle = [t for t in mj["tracks"] if t["category"] == "battle"]
        assert len(battle) >= 4


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
