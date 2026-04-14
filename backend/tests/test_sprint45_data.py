"""Tests for Sprint 45: Gym trainer teams, held item effects, save system.

These tests verify gym interior trainer rosters, held item battle effects,
and save system configuration/structure.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Gym Trainer Teams ───────────────────────────────────────

class TestGymTrainerTeams:
    def test_all_8_gyms(self):
        gt = _load_json("gym_trainer_teams.json")
        assert len(gt) == 8

    EXPECTED_GYMS = [
        "pewter_gym", "cerulean_gym", "vermilion_gym", "celadon_gym",
        "fuchsia_gym", "saffron_gym", "cinnabar_gym", "viridian_gym"
    ]

    @pytest.mark.parametrize("gym_id", EXPECTED_GYMS)
    def test_gym_exists(self, gym_id):
        gt = _load_json("gym_trainer_teams.json")
        assert gym_id in gt
        gym = gt[gym_id]
        assert "leader" in gym
        assert "trainers" in gym
        assert len(gym["trainers"]) >= 1

    def test_all_trainers_have_fields(self):
        gt = _load_json("gym_trainer_teams.json")
        for gid, gym in gt.items():
            for trainer in gym["trainers"]:
                assert "id" in trainer, f"trainer in {gid} missing id"
                assert "name" in trainer, f"trainer in {gid} missing name"
                assert "class" in trainer, f"trainer in {gid} missing class"
                assert "team" in trainer, f"trainer in {gid} missing team"
                assert len(trainer["team"]) >= 1

    def test_all_pokemon_have_fields(self):
        gt = _load_json("gym_trainer_teams.json")
        for gid, gym in gt.items():
            for trainer in gym["trainers"]:
                for pokemon in trainer["team"]:
                    assert "species" in pokemon
                    assert "level" in pokemon
                    assert "moves" in pokemon
                    assert len(pokemon["moves"]) >= 2

    def test_unique_trainer_ids(self):
        gt = _load_json("gym_trainer_teams.json")
        all_ids = []
        for gid, gym in gt.items():
            for trainer in gym["trainers"]:
                all_ids.append(trainer["id"])
        assert len(all_ids) == len(set(all_ids))

    def test_level_progression(self):
        gt = _load_json("gym_trainer_teams.json")
        gym_order = self.EXPECTED_GYMS
        prev_max = 0
        for gym_id in gym_order:
            gym = gt[gym_id]
            max_level = max(
                p["level"] for t in gym["trainers"] for p in t["team"]
            )
            assert max_level >= prev_max, \
                f"{gym_id} max level {max_level} < previous {prev_max}"
            prev_max = max_level

    def test_total_trainers(self):
        gt = _load_json("gym_trainer_teams.json")
        total = sum(len(gym["trainers"]) for gym in gt.values())
        assert total >= 18

    def test_viridian_gym_has_most_trainers(self):
        gt = _load_json("gym_trainer_teams.json")
        viridian_count = len(gt["viridian_gym"]["trainers"])
        for gid, gym in gt.items():
            if gid != "viridian_gym":
                assert len(gym["trainers"]) <= viridian_count


# ──── Held Item Effects ───────────────────────────────────────

class TestHeldItemEffects:
    def test_effect_count(self):
        effects = _load_json("held_item_effects.json")
        assert len(effects) == 18

    def test_all_have_required_fields(self):
        effects = _load_json("held_item_effects.json")
        for eid, data in effects.items():
            assert "name" in data, f"{eid} missing name"
            assert "trigger" in data, f"{eid} missing trigger"
            assert "effect" in data, f"{eid} missing effect"
            assert "description" in data, f"{eid} missing description"

    VALID_TRIGGERS = {
        "end_of_turn", "on_attack", "on_lethal_hit", "on_damage_dealt",
        "before_turn", "on_hit", "hp_below_half", "on_status_received",
        "on_pp_depleted"
    }

    def test_triggers_valid(self):
        effects = _load_json("held_item_effects.json")
        for eid, data in effects.items():
            assert data["trigger"] in self.VALID_TRIGGERS, \
                f"{eid} has invalid trigger: {data['trigger']}"

    def test_leftovers_heal(self):
        effects = _load_json("held_item_effects.json")
        lf = effects["leftovers"]
        assert lf["trigger"] == "end_of_turn"
        assert lf["amount"] == 6.25

    def test_choice_band_boost(self):
        effects = _load_json("held_item_effects.json")
        cb = effects["choice_band"]
        assert cb["multiplier"] == 1.5
        assert cb["restriction"] == "lock_move"

    def test_focus_sash_consumed(self):
        effects = _load_json("held_item_effects.json")
        fs = effects["focus_sash"]
        assert fs["consumed"] is True
        assert fs["condition"] == "full_hp"

    def test_life_orb_recoil(self):
        effects = _load_json("held_item_effects.json")
        lo = effects["life_orb"]
        assert lo["multiplier"] == 1.3
        assert lo["recoil_percent"] == 10

    def test_berry_effects_consumed(self):
        effects = _load_json("held_item_effects.json")
        berries = [eid for eid in effects if "berry" in eid]
        assert len(berries) >= 8
        for bid in berries:
            assert effects[bid]["consumed"] is True

    def test_status_cure_berries(self):
        effects = _load_json("held_item_effects.json")
        cure_berries = {eid: d for eid, d in effects.items()
                        if d.get("effect") == "cure_status"}
        assert len(cure_berries) >= 5

    def test_lum_berry_cures_any(self):
        effects = _load_json("held_item_effects.json")
        lum = effects["lum_berry"]
        assert lum["effect"] == "cure_any_status"

    def test_items_exist_in_items_json(self):
        effects = _load_json("held_item_effects.json")
        items = _load_json("items.json")
        item_names = {i["name"] for i in items}
        for eid, data in effects.items():
            assert data["name"] in item_names, \
                f"{data['name']} not found in items.json"


# ──── Save System ─────────────────────────────────────────────

class TestSaveSystem:
    def test_save_slots(self):
        ss = _load_json("save_system.json")
        assert ss["save_slots"] == 3

    def test_autosave_config(self):
        ss = _load_json("save_system.json")
        auto = ss["autosave"]
        assert auto["enabled"] is True
        assert auto["interval_seconds"] > 0
        assert len(auto["triggers"]) >= 2

    def test_save_data_structure(self):
        ss = _load_json("save_system.json")
        structure = ss["save_data_structure"]
        assert "header" in structure
        assert "player" in structure
        assert "position" in structure
        assert "party" in structure
        assert "pc_storage" in structure
        assert "pokedex" in structure
        assert "items" in structure
        assert "progress" in structure

    def test_party_max_6(self):
        ss = _load_json("save_system.json")
        assert ss["save_data_structure"]["party"]["max_size"] == 6

    def test_pc_storage_matches(self):
        ss = _load_json("save_system.json")
        pc = ss["save_data_structure"]["pc_storage"]
        assert pc["boxes"] == 12
        assert pc["per_box"] == 30

    def test_bag_pockets(self):
        ss = _load_json("save_system.json")
        pockets = ss["save_data_structure"]["items"]["bag_pockets"]
        assert "items" in pockets
        assert "key_items" in pockets
        assert "poke_balls" in pockets
        assert "berries" in pockets

    def test_validation(self):
        ss = _load_json("save_system.json")
        val = ss["validation"]
        assert val["backup_previous_save"] is True
        assert val["max_save_size_kb"] > 0

    def test_storage_format(self):
        ss = _load_json("save_system.json")
        assert ss["storage_format"] == "json"

    def test_pokemon_fields(self):
        ss = _load_json("save_system.json")
        fields = ss["save_data_structure"]["party"]["pokemon_fields"]
        assert "species_id" in fields
        assert "level" in fields
        assert "moves" in fields
        assert "current_hp" in fields
        assert "ivs" in fields
        assert "evs" in fields
        assert "nature" in fields

    def test_progress_tracking(self):
        ss = _load_json("save_system.json")
        progress = ss["save_data_structure"]["progress"]
        assert "story_flags" in progress
        assert "defeated_trainers" in progress
        assert "collected_items" in progress


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
