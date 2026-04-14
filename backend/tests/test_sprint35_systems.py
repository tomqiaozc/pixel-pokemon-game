"""Tests for Sprint 35: Safari Zone, fishing rods, day/night system.

These tests verify Safari Zone mechanics, fishing rod encounter tables,
and day/night time period definitions.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Safari Zone ──────────────────────────────────────────────

class TestSafariZone:
    def test_file_exists(self):
        safari = _load_json("safari_zone.json")
        assert "zones" in safari

    def test_entry_fee(self):
        safari = _load_json("safari_zone.json")
        assert safari["entry_fee"] == 500

    def test_safari_balls(self):
        safari = _load_json("safari_zone.json")
        assert safari["safari_balls"] == 30

    def test_max_steps(self):
        safari = _load_json("safari_zone.json")
        assert safari["max_steps"] == 600

    def test_zone_count(self):
        safari = _load_json("safari_zone.json")
        assert len(safari["zones"]) == 4

    ZONE_IDS = ["safari_zone_center", "safari_zone_east", "safari_zone_north", "safari_zone_west"]

    @pytest.mark.parametrize("zone_id", ZONE_IDS)
    def test_zone_exists(self, zone_id):
        safari = _load_json("safari_zone.json")
        found = next((z for z in safari["zones"] if z["id"] == zone_id), None)
        assert found is not None
        assert len(found["encounters"]) >= 5

    def test_chansey_in_safari(self):
        safari = _load_json("safari_zone.json")
        chansey_zones = 0
        for zone in safari["zones"]:
            if any(e["name"] == "Chansey" for e in zone["encounters"]):
                chansey_zones += 1
        assert chansey_zones >= 2

    def test_tauros_rare(self):
        safari = _load_json("safari_zone.json")
        for zone in safari["zones"]:
            tauros = next((e for e in zone["encounters"] if e["name"] == "Tauros"), None)
            if tauros:
                assert tauros["rate"] <= 5

    def test_bait_mechanics(self):
        safari = _load_json("safari_zone.json")
        bait = safari["mechanics"]["bait"]
        assert bait["flee_modifier"] == 0.5
        assert bait["catch_modifier"] == 0.5

    def test_rock_mechanics(self):
        safari = _load_json("safari_zone.json")
        rock = safari["mechanics"]["rock"]
        assert rock["flee_modifier"] == 2.0
        assert rock["catch_modifier"] == 2.0

    def test_safari_ball_catch_rate(self):
        safari = _load_json("safari_zone.json")
        assert safari["mechanics"]["safari_ball"]["catch_rate_multiplier"] == 1.5


# ──── Fishing Rods ─────────────────────────────────────────────

class TestFishingRods:
    def test_rod_count(self):
        rods = _load_json("fishing_rods.json")
        assert len(rods) == 3

    EXPECTED_RODS = ["old_rod", "good_rod", "super_rod"]

    @pytest.mark.parametrize("rod_id", EXPECTED_RODS)
    def test_rod_exists(self, rod_id):
        rods = _load_json("fishing_rods.json")
        assert rod_id in rods
        rod = rods[rod_id]
        assert "name" in rod
        assert "encounter_table" in rod
        assert "obtainable_location" in rod

    def test_old_rod_magikarp_only(self):
        rods = _load_json("fishing_rods.json")
        encounters = rods["old_rod"]["encounter_table"]
        assert len(encounters) == 1
        assert encounters[0]["name"] == "Magikarp"
        assert encounters[0]["rate"] == 100

    def test_good_rod_variety(self):
        rods = _load_json("fishing_rods.json")
        encounters = rods["good_rod"]["encounter_table"]
        assert len(encounters) >= 4

    def test_super_rod_best_variety(self):
        rods = _load_json("fishing_rods.json")
        encounters = rods["super_rod"]["encounter_table"]
        assert len(encounters) >= 10

    def test_super_rod_has_gyarados(self):
        rods = _load_json("fishing_rods.json")
        names = [e["name"] for e in rods["super_rod"]["encounter_table"]]
        assert "Gyarados" in names

    def test_encounter_rates_valid(self):
        rods = _load_json("fishing_rods.json")
        for rod_id, rod in rods.items():
            total = sum(e["rate"] for e in rod["encounter_table"])
            assert total == 100, f"{rod_id} rates sum to {total}, expected 100"

    def test_rod_progression(self):
        rods = _load_json("fishing_rods.json")
        old_count = len(rods["old_rod"]["encounter_table"])
        good_count = len(rods["good_rod"]["encounter_table"])
        super_count = len(rods["super_rod"]["encounter_table"])
        assert old_count < good_count < super_count


# ──── Day/Night System ─────────────────────────────────────────

class TestDayNightSystem:
    def test_file_exists(self):
        dn = _load_json("day_night.json")
        assert "time_periods" in dn

    def test_four_periods(self):
        dn = _load_json("day_night.json")
        assert len(dn["time_periods"]) == 4

    EXPECTED_PERIODS = ["morning", "day", "evening", "night"]

    @pytest.mark.parametrize("period", EXPECTED_PERIODS)
    def test_period_exists(self, period):
        dn = _load_json("day_night.json")
        assert period in dn["time_periods"]
        p = dn["time_periods"][period]
        assert "name" in p
        assert "start_hour" in p
        assert "end_hour" in p
        assert "ambient_light" in p

    def test_day_brightest(self):
        dn = _load_json("day_night.json")
        assert dn["time_periods"]["day"]["ambient_light"] == 1.0

    def test_night_darkest(self):
        dn = _load_json("day_night.json")
        assert dn["time_periods"]["night"]["ambient_light"] == 0.3

    def test_encounter_modifiers_exist(self):
        dn = _load_json("day_night.json")
        assert len(dn["encounter_modifiers"]) == 4

    def test_night_ghost_boost(self):
        dn = _load_json("day_night.json")
        assert "ghost" in dn["encounter_modifiers"]["night"]["increased_types"]

    def test_day_ghost_decrease(self):
        dn = _load_json("day_night.json")
        assert "ghost" in dn["encounter_modifiers"]["day"]["decreased_types"]

    def test_night_higher_encounter_rate(self):
        dn = _load_json("day_night.json")
        assert dn["encounter_modifiers"]["night"]["rate_modifier"] > 1.0

    def test_special_events(self):
        dn = _load_json("day_night.json")
        assert "full_moon" in dn["special_events"]
        assert "dawn" in dn["special_events"]
        assert "dusk" in dn["special_events"]

    def test_full_moon_boost(self):
        dn = _load_json("day_night.json")
        fm = dn["special_events"]["full_moon"]
        assert fm["encounter_rate_modifier"] == 1.5
        assert "clefairy_encounter_boost" in fm["effects"]


# ──── Counts ───────────────────────────────────────────────────

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

    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132
