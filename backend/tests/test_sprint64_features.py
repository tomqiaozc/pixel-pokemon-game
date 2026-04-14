"""Tests for Sprint 64: Move tutor, Safari Zone config, Game Corner.

These tests verify move tutor NPC data, Safari Zone encounter tables
and mechanics, and Game Corner enhancements.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Move Tutor ────────────────────────────────────────────

class TestMoveTutor:
    def test_tutor_count(self):
        mt = _load_json("move_tutor.json")
        assert len(mt["tutors"]) == 10

    def test_tutors_have_fields(self):
        mt = _load_json("move_tutor.json")
        for t in mt["tutors"]:
            assert "id" in t
            assert "location" in t
            assert "move" in t
            assert "cost_type" in t
            assert "cost" in t

    def test_unique_tutor_ids(self):
        mt = _load_json("move_tutor.json")
        ids = [t["id"] for t in mt["tutors"]]
        assert len(ids) == len(set(ids))

    def test_valid_cost_types(self):
        mt = _load_json("move_tutor.json")
        valid = set(mt["cost_types"])
        for t in mt["tutors"]:
            assert t["cost_type"] in valid, \
                f"{t['id']} has invalid cost_type: {t['cost_type']}"

    def test_free_tutors_cost_zero(self):
        mt = _load_json("move_tutor.json")
        for t in mt["tutors"]:
            if t["cost_type"] == "free":
                assert t["cost"] == 0, f"{t['id']} is free but cost != 0"

    def test_paid_tutors_cost_positive(self):
        mt = _load_json("move_tutor.json")
        for t in mt["tutors"]:
            if t["cost_type"] != "free":
                assert t["cost"] > 0, f"{t['id']} paid but cost <= 0"

    def test_moves_exist(self):
        mt = _load_json("move_tutor.json")
        moves = _load_json("moves.json")
        move_names = set(moves.keys())
        for t in mt["tutors"]:
            assert t["move"] in move_names, \
                f"Move tutor teaches {t['move']} which is not in moves.json"

    def test_dialogue_templates(self):
        mt = _load_json("move_tutor.json")
        d = mt["dialogue"]
        assert len(d) == 6
        assert "{move}" in d["offer"]


# ──── Safari Zone Config ───────────────────────────────────

class TestSafariZoneConfig:
    def test_entrance_fee(self):
        sz = _load_json("safari_zone_config.json")
        assert sz["safari_zone"]["entrance_fee"] == 500

    def test_step_limit(self):
        sz = _load_json("safari_zone_config.json")
        assert sz["safari_zone"]["step_limit"] == 500

    def test_safari_balls(self):
        sz = _load_json("safari_zone_config.json")
        assert sz["safari_zone"]["safari_balls"] == 30

    def test_area_count(self):
        sz = _load_json("safari_zone_config.json")
        assert len(sz["areas"]) == 4

    def test_areas_have_fields(self):
        sz = _load_json("safari_zone_config.json")
        for area in sz["areas"]:
            assert "id" in area
            assert "name" in area
            assert "encounters" in area
            assert len(area["encounters"]) >= 1

    def test_encounters_have_fields(self):
        sz = _load_json("safari_zone_config.json")
        for area in sz["areas"]:
            for enc in area["encounters"]:
                assert "pokemon" in enc
                assert "level_range" in enc
                assert "rate" in enc

    def test_bait_mechanics(self):
        sz = _load_json("safari_zone_config.json")
        bait = sz["mechanics"]["bait"]
        assert bait["flee_modifier"] < 0  # lowers flee
        assert bait["catch_modifier"] < 0  # lowers catch

    def test_rock_mechanics(self):
        sz = _load_json("safari_zone_config.json")
        rock = sz["mechanics"]["rock"]
        assert rock["catch_modifier"] > 0  # raises catch
        assert rock["flee_modifier"] > 0  # raises flee

    def test_chansey_available(self):
        sz = _load_json("safari_zone_config.json")
        all_pokemon = set()
        for area in sz["areas"]:
            for enc in area["encounters"]:
                all_pokemon.add(enc["pokemon"])
        assert "Chansey" in all_pokemon

    def test_postgame_expansion(self):
        sz = _load_json("safari_zone_config.json")
        pe = sz["postgame_expansion"]
        assert pe["enabled"] is True
        assert pe["unlock_trigger"] == "champion_defeated"


# ──── Game Corner Enhancements ─────────────────────────────

class TestGameCornerEnhancements:
    def test_coin_case_required(self):
        gc = _load_json("game_corner.json")
        assert gc["coin_case_required"] is True

    def test_max_coins(self):
        gc = _load_json("game_corner.json")
        assert gc["max_coins"] == 9999

    def test_npc_hints(self):
        gc = _load_json("game_corner.json")
        assert len(gc["npc_hints"]) == 4

    def test_rocket_hideout_event(self):
        gc = _load_json("game_corner.json")
        rh = gc["team_rocket_hideout"]
        assert rh["requires_event"] == "investigate_game_corner"


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
