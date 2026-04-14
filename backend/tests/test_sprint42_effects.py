"""Tests for Sprint 42: Move effects, ability effects, field effects.

These tests verify secondary move effects, ability battle triggers,
and field/hazard effects data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Move Effects ────────────────────────────────────────────

class TestMoveEffects:
    def test_effect_count(self):
        effects = _load_json("move_effects.json")
        assert len(effects) == 40

    def test_all_have_secondary(self):
        effects = _load_json("move_effects.json")
        for move, data in effects.items():
            assert "secondary" in data, f"{move} missing secondary"

    def test_all_secondaries_have_type(self):
        effects = _load_json("move_effects.json")
        for move, data in effects.items():
            assert "type" in data["secondary"], f"{move} secondary missing type"

    VALID_SECONDARY_TYPES = {
        "status", "flinch", "recoil", "recharge", "stat_change",
        "drain", "self_faint", "random_status"
    }

    def test_secondary_types_valid(self):
        effects = _load_json("move_effects.json")
        for move, data in effects.items():
            assert data["secondary"]["type"] in self.VALID_SECONDARY_TYPES, \
                f"{move} has invalid secondary type: {data['secondary']['type']}"

    def test_status_effects_have_status_and_chance(self):
        effects = _load_json("move_effects.json")
        status_moves = {m: d for m, d in effects.items()
                        if d["secondary"]["type"] == "status"}
        assert len(status_moves) >= 10
        for move, data in status_moves.items():
            assert "status" in data["secondary"], f"{move} missing status"
            assert "chance" in data["secondary"], f"{move} missing chance"
            assert 1 <= data["secondary"]["chance"] <= 100

    def test_flinch_effects(self):
        effects = _load_json("move_effects.json")
        flinch_moves = [m for m, d in effects.items()
                        if d["secondary"]["type"] == "flinch"]
        assert len(flinch_moves) >= 4

    def test_recoil_effects(self):
        effects = _load_json("move_effects.json")
        recoil_moves = {m: d for m, d in effects.items()
                        if d["secondary"]["type"] == "recoil"}
        assert len(recoil_moves) >= 3
        for move, data in recoil_moves.items():
            assert "percent" in data["secondary"]
            assert data["secondary"]["percent"] > 0

    def test_drain_effects(self):
        effects = _load_json("move_effects.json")
        drain_moves = {m: d for m, d in effects.items()
                       if d["secondary"]["type"] == "drain"}
        assert len(drain_moves) >= 3
        for move, data in drain_moves.items():
            assert data["secondary"]["percent"] == 50

    def test_self_faint_effects(self):
        effects = _load_json("move_effects.json")
        faint_moves = [m for m, d in effects.items()
                       if d["secondary"]["type"] == "self_faint"]
        assert "Self Destruct" in faint_moves
        assert "Explosion" in faint_moves

    def test_stat_change_effects(self):
        effects = _load_json("move_effects.json")
        stat_moves = {m: d for m, d in effects.items()
                      if d["secondary"]["type"] == "stat_change"}
        assert len(stat_moves) >= 8
        for move, data in stat_moves.items():
            sec = data["secondary"]
            assert "stat" in sec
            assert "stages" in sec
            assert "target" in sec
            assert sec["target"] in ("self", "opponent")

    def test_self_boost_moves(self):
        effects = _load_json("move_effects.json")
        self_boosts = [m for m, d in effects.items()
                       if d["secondary"]["type"] == "stat_change"
                       and d["secondary"]["target"] == "self"]
        assert "Swords Dance" in self_boosts
        assert "Agility" in self_boosts
        assert "Amnesia" in self_boosts

    def test_swords_dance_stages(self):
        effects = _load_json("move_effects.json")
        sd = effects["Swords Dance"]["secondary"]
        assert sd["stat"] == "attack"
        assert sd["stages"] == 2

    def test_tri_attack_random_status(self):
        effects = _load_json("move_effects.json")
        tri = effects["Tri Attack"]["secondary"]
        assert tri["type"] == "random_status"
        assert set(tri["statuses"]) == {"burn", "freeze", "paralysis"}

    def test_hyper_beam_recharge(self):
        effects = _load_json("move_effects.json")
        hb = effects["Hyper Beam"]["secondary"]
        assert hb["type"] == "recharge"
        assert hb["turns"] == 1

    def test_moves_exist_in_moves_json(self):
        effects = _load_json("move_effects.json")
        moves = _load_json("moves.json")
        for move_name in effects:
            assert move_name in moves, f"{move_name} not found in moves.json"


# ──── Ability Effects ─────────────────────────────────────────

class TestAbilityEffects:
    def test_ability_count(self):
        abilities = _load_json("ability_effects.json")
        assert len(abilities) == 31

    def test_all_have_trigger(self):
        abilities = _load_json("ability_effects.json")
        for aid, data in abilities.items():
            assert "trigger" in data, f"{aid} missing trigger"

    def test_all_have_effect(self):
        abilities = _load_json("ability_effects.json")
        for aid, data in abilities.items():
            assert "effect" in data, f"{aid} missing effect"

    VALID_TRIGGERS = {
        "hp_below_third", "on_contact_received", "hit_by_type",
        "on_switch_in", "on_status_received", "has_status",
        "passive", "on_switch_out", "hit_by_ohko",
        "end_of_turn", "in_weather"
    }

    def test_triggers_valid(self):
        abilities = _load_json("ability_effects.json")
        for aid, data in abilities.items():
            assert data["trigger"] in self.VALID_TRIGGERS, \
                f"{aid} has invalid trigger: {data['trigger']}"

    def test_starter_abilities(self):
        abilities = _load_json("ability_effects.json")
        for ab in ("overgrow", "blaze", "torrent"):
            assert ab in abilities
            assert abilities[ab]["trigger"] == "hp_below_third"
            assert abilities[ab]["multiplier"] == 1.5

    def test_contact_abilities(self):
        abilities = _load_json("ability_effects.json")
        contact = {a: d for a, d in abilities.items()
                   if d["trigger"] == "on_contact_received"}
        assert len(contact) >= 3
        for aid, data in contact.items():
            assert "chance" in data
            assert "status" in data

    def test_type_absorb_abilities(self):
        abilities = _load_json("ability_effects.json")
        absorb = {a: d for a, d in abilities.items()
                  if d["trigger"] == "hit_by_type" and d.get("negate_damage")}
        assert len(absorb) >= 3
        for aid, data in absorb.items():
            assert "type" in data

    def test_water_absorb(self):
        abilities = _load_json("ability_effects.json")
        wa = abilities["water_absorb"]
        assert wa["type"] == "water"
        assert wa["negate_damage"] is True
        assert wa["amount"] == 25

    def test_levitate_ground_immunity(self):
        abilities = _load_json("ability_effects.json")
        lev = abilities["levitate"]
        assert lev["type"] == "ground"
        assert lev["effect"] == "immune"

    def test_intimidate(self):
        abilities = _load_json("ability_effects.json")
        intim = abilities["intimidate"]
        assert intim["trigger"] == "on_switch_in"
        assert intim["stat"] == "attack"
        assert intim["stages"] == -1

    def test_passive_abilities(self):
        abilities = _load_json("ability_effects.json")
        passive = {a: d for a, d in abilities.items()
                   if d["trigger"] == "passive"}
        assert len(passive) >= 6

    def test_status_prevention_abilities(self):
        abilities = _load_json("ability_effects.json")
        preventers = {a: d for a, d in abilities.items()
                      if d.get("effect") == "prevent_status"}
        assert len(preventers) >= 4

    def test_weather_abilities(self):
        abilities = _load_json("ability_effects.json")
        weather = {a: d for a, d in abilities.items()
                   if d["trigger"] == "in_weather"}
        assert len(weather) >= 4
        for aid, data in weather.items():
            assert "weather" in data

    def test_shed_skin(self):
        abilities = _load_json("ability_effects.json")
        ss = abilities["shed_skin"]
        assert ss["trigger"] == "end_of_turn"
        assert ss["chance"] == 30

    def test_synchronize_statuses(self):
        abilities = _load_json("ability_effects.json")
        sync = abilities["synchronize"]
        assert set(sync["statuses"]) == {"burn", "poison", "paralysis"}


# ──── Field Effects ───────────────────────────────────────────

class TestFieldEffects:
    def test_field_effect_count(self):
        fields = _load_json("field_effects.json")
        assert len(fields) == 8

    def test_all_have_name(self):
        fields = _load_json("field_effects.json")
        for fid, data in fields.items():
            assert "name" in data, f"{fid} missing name"

    def test_all_have_type(self):
        fields = _load_json("field_effects.json")
        for fid, data in fields.items():
            assert "type" in data, f"{fid} missing type"

    def test_all_have_effect(self):
        fields = _load_json("field_effects.json")
        for fid, data in fields.items():
            assert "effect" in data, f"{fid} missing effect"

    def test_all_have_description(self):
        fields = _load_json("field_effects.json")
        for fid, data in fields.items():
            assert "description" in data, f"{fid} missing description"

    VALID_TYPES = {"screen", "protection", "hazard", "entry_hazard"}

    def test_field_types_valid(self):
        fields = _load_json("field_effects.json")
        for fid, data in fields.items():
            assert data["type"] in self.VALID_TYPES, \
                f"{fid} has invalid type: {data['type']}"

    def test_screens(self):
        fields = _load_json("field_effects.json")
        screens = {f: d for f, d in fields.items() if d["type"] == "screen"}
        assert len(screens) == 2
        assert "reflect" in screens
        assert "light_screen" in screens

    def test_screen_duration(self):
        fields = _load_json("field_effects.json")
        assert fields["reflect"]["duration_turns"] == 5
        assert fields["light_screen"]["duration_turns"] == 5

    def test_reflect_halves_physical(self):
        fields = _load_json("field_effects.json")
        assert fields["reflect"]["effect"] == "halve_physical_damage"

    def test_light_screen_halves_special(self):
        fields = _load_json("field_effects.json")
        assert fields["light_screen"]["effect"] == "halve_special_damage"

    def test_entry_hazards(self):
        fields = _load_json("field_effects.json")
        hazards = {f: d for f, d in fields.items()
                   if d["type"] == "entry_hazard"}
        assert len(hazards) == 3
        assert "stealth_rock" in hazards
        assert "spikes" in hazards
        assert "toxic_spikes" in hazards

    def test_spikes_layers(self):
        fields = _load_json("field_effects.json")
        spikes = fields["spikes"]
        assert spikes["max_layers"] == 3
        assert "1" in spikes["layer_damage"]
        assert "3" in spikes["layer_damage"]

    def test_toxic_spikes_layers(self):
        fields = _load_json("field_effects.json")
        ts = fields["toxic_spikes"]
        assert ts["max_layers"] == 2
        assert ts["layer_effects"]["1"] == "poison"
        assert ts["layer_effects"]["2"] == "badly_poisoned"

    def test_stealth_rock_type_effectiveness(self):
        fields = _load_json("field_effects.json")
        sr = fields["stealth_rock"]
        assert sr["type_effectiveness_applied"] is True
        assert sr["base_damage_percent"] == 12.5

    def test_leech_seed(self):
        fields = _load_json("field_effects.json")
        ls = fields["leech_seed"]
        assert ls["type"] == "hazard"
        assert ls["drain_percent"] == 12.5

    def test_protections(self):
        fields = _load_json("field_effects.json")
        protections = {f: d for f, d in fields.items()
                       if d["type"] == "protection"}
        assert len(protections) == 2
        assert "mist" in protections
        assert "safeguard" in protections

    def test_all_have_set_by_move(self):
        fields = _load_json("field_effects.json")
        for fid, data in fields.items():
            assert "set_by_move" in data, f"{fid} missing set_by_move"


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
