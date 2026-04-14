"""Tests for Sprint 63: Battle frontier, berry system, daycare.

These tests verify Battle Tower configuration, berry growing mechanics,
and Pokemon daycare/breeding system.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Battle Frontier ──────────────────────────────────────

class TestBattleFrontier:
    def test_unlock_requirement(self):
        bf = _load_json("battle_frontier.json")
        assert bf["battle_tower"]["unlock_requirement"] == "champion_defeated"

    def test_levels_per_set(self):
        bf = _load_json("battle_frontier.json")
        assert bf["battle_tower"]["levels_per_set"] == 7

    def test_rules_team_size(self):
        bf = _load_json("battle_frontier.json")
        assert bf["rules"]["team_size"] == 3
        assert bf["rules"]["level_cap"] == 50

    def test_species_clause(self):
        bf = _load_json("battle_frontier.json")
        assert bf["rules"]["species_clause"] is True
        assert bf["rules"]["item_clause"] is True

    def test_banned_pokemon(self):
        bf = _load_json("battle_frontier.json")
        banned = bf["rules"]["banned_pokemon"]
        assert "Mewtwo" in banned
        assert "Mew" in banned

    def test_no_healing(self):
        bf = _load_json("battle_frontier.json")
        assert bf["rules"]["healing_between_battles"] is False

    def test_bp_rewards(self):
        bf = _load_json("battle_frontier.json")
        r = bf["rewards"]
        assert r["currency"] == "battle_points"
        assert r["bp_per_win"] >= 1

    def test_shop_items(self):
        bf = _load_json("battle_frontier.json")
        shop = bf["rewards"]["shop_items"]
        assert len(shop) == 13
        for item in shop:
            assert "item" in item
            assert "cost" in item
            assert item["cost"] > 0

    def test_trainer_pool(self):
        bf = _load_json("battle_frontier.json")
        pool = bf["trainer_pool"]
        assert len(pool) == 8
        for t in pool:
            assert "class" in t
            assert "ai_level" in t

    def test_tower_tycoon(self):
        bf = _load_json("battle_frontier.json")
        tt = bf["tower_tycoon"]
        assert tt["ai_level"] == "expert"
        assert len(tt["appears_at_streak"]) == 2


# ──── Berry System ─────────────────────────────────────────

class TestBerrySystem:
    def test_berry_count(self):
        bs = _load_json("berry_system.json")
        assert len(bs["berries"]) == 12

    def test_berries_have_fields(self):
        bs = _load_json("berry_system.json")
        for berry in bs["berries"]:
            assert "id" in berry
            assert "name" in berry
            assert "effect" in berry
            assert "growth_hours" in berry
            assert "yield_min" in berry
            assert "yield_max" in berry

    def test_unique_berry_ids(self):
        bs = _load_json("berry_system.json")
        ids = [b["id"] for b in bs["berries"]]
        assert len(ids) == len(set(ids))

    def test_yield_range_valid(self):
        bs = _load_json("berry_system.json")
        for berry in bs["berries"]:
            assert berry["yield_min"] <= berry["yield_max"], \
                f"{berry['id']} yield_min > yield_max"
            assert berry["yield_min"] >= 1

    def test_growth_stages(self):
        bs = _load_json("berry_system.json")
        assert len(bs["growth_stages"]) == 5

    def test_growth_stages_have_fields(self):
        bs = _load_json("berry_system.json")
        for stage in bs["growth_stages"]:
            assert "id" in stage
            assert "name" in stage
            assert "sprite" in stage

    def test_watering_config(self):
        bs = _load_json("berry_system.json")
        w = bs["watering"]
        assert w["bonus_per_water"] >= 1
        assert w["wither_after_ready_hours"] > 0

    def test_soil_patches(self):
        bs = _load_json("berry_system.json")
        patches = bs["soil_patches"]
        assert len(patches) == 7
        total = sum(p["slots"] for p in patches)
        assert total == bs["total_soil_slots"]

    def test_status_cure_berries(self):
        bs = _load_json("berry_system.json")
        cure_effects = {"cure_paralysis", "cure_sleep", "cure_poison",
                        "cure_burn", "cure_freeze"}
        berry_effects = {b["effect"] for b in bs["berries"]}
        assert cure_effects.issubset(berry_effects)

    def test_berry_pouch(self):
        bs = _load_json("berry_system.json")
        bp = bs["berry_pouch"]
        assert bp["enabled"] is True
        assert bp["max_per_berry"] == 99


# ──── Daycare System ───────────────────────────────────────

class TestDaycareSystem:
    def test_daycare_location(self):
        dc = _load_json("daycare_system.json")
        assert dc["daycare"]["location"] == "route_5"

    def test_max_pokemon(self):
        dc = _load_json("daycare_system.json")
        assert dc["daycare"]["max_pokemon"] == 2

    def test_leveling_config(self):
        dc = _load_json("daycare_system.json")
        lv = dc["leveling"]
        assert lv["exp_per_step"] >= 1
        assert lv["evolution_enabled"] is False
        assert lv["move_learning"] == "replace_oldest"

    def test_breeding_enabled(self):
        dc = _load_json("daycare_system.json")
        assert dc["breeding"]["enabled"] is True

    def test_egg_groups(self):
        dc = _load_json("daycare_system.json")
        groups = dc["breeding"]["egg_groups"]
        assert len(groups) == 15
        assert "ditto" in groups
        assert "undiscovered" in groups

    def test_ditto_compatibility(self):
        dc = _load_json("daycare_system.json")
        br = dc["breeding"]
        assert br["ditto_compatible"] is True
        assert br["ditto_breeds_with_all"] is True

    def test_legendary_cannot_breed(self):
        dc = _load_json("daycare_system.json")
        assert dc["breeding"]["legendary_cannot_breed"] is True

    def test_compatibility_levels(self):
        dc = _load_json("daycare_system.json")
        comp = dc["compatibility"]
        assert len(comp) == 5
        assert comp["incompatible"]["chance"] == 0.0
        assert comp["same_species_different_ot"]["chance"] > comp["different_species_same_ot"]["chance"]

    def test_egg_mechanics(self):
        dc = _load_json("daycare_system.json")
        em = dc["egg_mechanics"]
        assert em["species_from_mother"] is True
        assert em["iv_inheritance"] == 3
        assert em["hatch_level"] == 5

    def test_dialogue_templates(self):
        dc = _load_json("daycare_system.json")
        d = dc["dialogue"]
        assert len(d) == 5
        assert "{pokemon}" in d["deposit"]
        assert "{cost}" in d["withdraw"]


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
