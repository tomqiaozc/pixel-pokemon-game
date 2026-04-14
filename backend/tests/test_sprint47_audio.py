"""Tests for Sprint 47: Pokemon cries, damage formula, NPC schedules.

These tests verify species sound parameters, damage calculation config,
and time-based NPC behavior schedules.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Pokemon Cries ───────────────────────────────────────────

class TestPokemonCries:
    def test_cry_count(self):
        cries = _load_json("pokemon_cries.json")
        assert len(cries) >= 146

    def test_all_have_fields(self):
        cries = _load_json("pokemon_cries.json")
        for name, data in cries.items():
            assert "base_pitch" in data, f"{name} missing base_pitch"
            assert "duration_ms" in data, f"{name} missing duration_ms"
            assert "waveform" in data, f"{name} missing waveform"
            assert "volume" in data, f"{name} missing volume"

    VALID_WAVEFORMS = {"square", "sawtooth", "triangle", "sine", "noise"}

    def test_waveforms_valid(self):
        cries = _load_json("pokemon_cries.json")
        for name, data in cries.items():
            assert data["waveform"] in self.VALID_WAVEFORMS, \
                f"{name} has invalid waveform: {data['waveform']}"

    def test_pitches_positive(self):
        cries = _load_json("pokemon_cries.json")
        for name, data in cries.items():
            assert data["base_pitch"] > 0, f"{name} pitch not positive"

    def test_durations_positive(self):
        cries = _load_json("pokemon_cries.json")
        for name, data in cries.items():
            assert data["duration_ms"] > 0, f"{name} duration not positive"

    def test_volumes_valid(self):
        cries = _load_json("pokemon_cries.json")
        for name, data in cries.items():
            assert 0 < data["volume"] <= 1.0, f"{name} volume out of range"

    def test_starters_have_cries(self):
        cries = _load_json("pokemon_cries.json")
        assert "Bulbasaur" in cries
        assert "Charmander" in cries
        assert "Squirtle" in cries

    def test_pikachu_has_cry(self):
        cries = _load_json("pokemon_cries.json")
        assert "Pikachu" in cries

    def test_species_match(self):
        cries = _load_json("pokemon_cries.json")
        species = _load_json("pokemon_species.json")
        species_names = {s["name"] for s in species}
        for cry_name in cries:
            assert cry_name in species_names, \
                f"{cry_name} not in pokemon_species.json"


# ──── Damage Formula ─────────────────────────────────────────

class TestDamageFormula:
    def test_has_base_formula(self):
        df = _load_json("damage_formula.json")
        assert "base_formula" in df
        assert "description" in df["base_formula"]

    def test_stab_multiplier(self):
        df = _load_json("damage_formula.json")
        assert df["modifiers"]["stab"]["multiplier"] == 1.5

    def test_type_effectiveness(self):
        df = _load_json("damage_formula.json")
        te = df["modifiers"]["type_effectiveness"]
        assert te["super_effective"] == 2.0
        assert te["not_very_effective"] == 0.5
        assert te["immune"] == 0.0

    def test_critical_hit_stages(self):
        df = _load_json("damage_formula.json")
        crit = df["modifiers"]["critical_hit"]
        assert crit["multiplier"] == 1.5
        assert crit["stages"]["0"] == 6.25
        assert len(crit["stages"]) >= 5

    def test_high_crit_moves(self):
        df = _load_json("damage_formula.json")
        hcm = df["modifiers"]["critical_hit"]["high_crit_moves"]
        assert "Slash" in hcm
        assert "Karate Chop" in hcm

    def test_random_factor(self):
        df = _load_json("damage_formula.json")
        rf = df["modifiers"]["random_factor"]
        assert rf["min"] == 0.85
        assert rf["max"] == 1.0

    def test_burn_modifier(self):
        df = _load_json("damage_formula.json")
        burn = df["modifiers"]["burn"]
        assert burn["physical_multiplier"] == 0.5
        assert burn["applies_to"] == "physical"

    def test_weather_modifiers(self):
        df = _load_json("damage_formula.json")
        weather = df["modifiers"]["weather"]
        assert weather["sun_fire_boost"] == 1.5
        assert weather["rain_water_boost"] == 1.5

    def test_minimum_damage(self):
        df = _load_json("damage_formula.json")
        assert df["minimum_damage"] == 1

    def test_stat_stages(self):
        df = _load_json("damage_formula.json")
        stages = df["stat_stages"]
        assert stages["min"] == -6
        assert stages["max"] == 6
        assert stages["multipliers"]["0"] == 1.0
        assert stages["multipliers"]["6"] == 4.0
        assert stages["multipliers"]["-6"] == 0.25

    def test_category_mapping(self):
        df = _load_json("damage_formula.json")
        mapping = df["category_stat_mapping"]
        assert mapping["physical"]["attack_stat"] == "attack"
        assert mapping["special"]["attack_stat"] == "sp_attack"

    def test_fixed_damage_moves(self):
        df = _load_json("damage_formula.json")
        fixed = df["fixed_damage_moves"]
        assert fixed["Sonic Boom"]["damage"] == 20
        assert fixed["Dragon Rage"]["damage"] == 40

    def test_multi_hit_moves(self):
        df = _load_json("damage_formula.json")
        multi = df["multi_hit_moves"]
        assert len(multi) >= 7
        assert multi["Double Kick"]["hits"] == 2

    def test_application_order(self):
        df = _load_json("damage_formula.json")
        order = df["application_order"]
        assert order[0] == "base_damage"
        assert "stab" in order
        assert "type_effectiveness" in order


# ──── NPC Schedules ───────────────────────────────────────────

class TestNPCSchedules:
    def test_schedule_count(self):
        schedules = _load_json("npc_schedules.json")
        assert len(schedules) == 12

    def test_all_have_fields(self):
        schedules = _load_json("npc_schedules.json")
        for npc in schedules:
            assert "npc_id" in npc
            assert "name" in npc
            assert "schedules" in npc

    VALID_PERIODS = {"morning", "day", "evening", "night"}

    def test_all_have_four_periods(self):
        schedules = _load_json("npc_schedules.json")
        for npc in schedules:
            periods = {s["period"] for s in npc["schedules"]}
            assert periods == self.VALID_PERIODS, \
                f"{npc['npc_id']} missing periods: {self.VALID_PERIODS - periods}"

    def test_schedules_have_location(self):
        schedules = _load_json("npc_schedules.json")
        for npc in schedules:
            for sched in npc["schedules"]:
                assert "location" in sched
                assert "x" in sched
                assert "y" in sched
                assert "activity" in sched

    def test_unique_npc_ids(self):
        schedules = _load_json("npc_schedules.json")
        ids = [n["npc_id"] for n in schedules]
        assert len(ids) == len(set(ids))

    def test_oak_in_lab(self):
        schedules = _load_json("npc_schedules.json")
        oak = next(n for n in schedules if n["npc_id"] == "pallet_prof_oak")
        morning = next(s for s in oak["schedules"] if s["period"] == "morning")
        assert morning["location"] == "oaks_lab"

    def test_nurse_always_available(self):
        schedules = _load_json("npc_schedules.json")
        nurse = next(n for n in schedules if n["npc_id"] == "viridian_nurse")
        for sched in nurse["schedules"]:
            assert sched["location"] == "viridian_pokecenter"

    def test_mr_fuji_tower_during_day(self):
        schedules = _load_json("npc_schedules.json")
        fuji = next(n for n in schedules if n["npc_id"] == "lavender_mr_fuji")
        day = next(s for s in fuji["schedules"] if s["period"] == "day")
        assert day["location"] == "pokemon_tower"

    def test_coordinates_non_negative(self):
        schedules = _load_json("npc_schedules.json")
        for npc in schedules:
            for sched in npc["schedules"]:
                assert sched["x"] >= 0
                assert sched["y"] >= 0


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
