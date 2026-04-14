"""Tests for Sprint 66: Pokemart inventory, gym puzzles, badge effects.

These tests verify shop inventories, gym puzzle configs,
and badge effect enhancements.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Pokemart Inventory ───────────────────────────────────

class TestPokemartInventory:
    def test_shop_count(self):
        pm = _load_json("pokemart_inventory.json")
        assert len(pm["shops"]) == 10

    def test_shops_have_fields(self):
        pm = _load_json("pokemart_inventory.json")
        for shop in pm["shops"]:
            assert "id" in shop
            assert "name" in shop
            assert "base_stock" in shop
            assert len(shop["base_stock"]) >= 1

    def test_unique_shop_ids(self):
        pm = _load_json("pokemart_inventory.json")
        ids = [s["id"] for s in pm["shops"]]
        assert len(ids) == len(set(ids))

    def test_stock_items_have_price(self):
        pm = _load_json("pokemart_inventory.json")
        for shop in pm["shops"]:
            for item in shop["base_stock"]:
                assert "item" in item
                assert "price" in item
                assert item["price"] > 0

    def test_celadon_is_department_store(self):
        pm = _load_json("pokemart_inventory.json")
        celadon = next(s for s in pm["shops"] if s["id"] == "celadon_city")
        assert celadon.get("is_department_store") is True
        assert len(celadon["base_stock"]) >= 10

    def test_badge_unlock_count(self):
        pm = _load_json("pokemart_inventory.json")
        assert len(pm["badge_unlocks"]) == 8

    def test_badge_unlocks_progression(self):
        pm = _load_json("pokemart_inventory.json")
        badges = [u["badges"] for u in pm["badge_unlocks"]]
        assert badges == sorted(badges)

    def test_sell_multiplier(self):
        pm = _load_json("pokemart_inventory.json")
        assert pm["sell_multiplier"] == 0.5

    def test_indigo_plateau_has_full_restore(self):
        pm = _load_json("pokemart_inventory.json")
        ip = next(s for s in pm["shops"] if s["id"] == "indigo_plateau")
        items = {i["item"] for i in ip["base_stock"]}
        assert "Full Restore" in items


# ──── Gym Puzzles ──────────────────────────────────────────

class TestGymPuzzles:
    def test_gym_count(self):
        gp = _load_json("gym_puzzles.json")
        assert len(gp["gyms"]) == 8

    def test_gyms_have_fields(self):
        gp = _load_json("gym_puzzles.json")
        for gym in gp["gyms"]:
            assert "id" in gym
            assert "leader" in gym
            assert "puzzle_type" in gym
            assert "trainers_before_leader" in gym

    def test_unique_gym_ids(self):
        gp = _load_json("gym_puzzles.json")
        ids = [g["id"] for g in gp["gyms"]]
        assert len(ids) == len(set(ids))

    def test_valid_puzzle_types(self):
        gp = _load_json("gym_puzzles.json")
        valid = set(gp["puzzle_types"])
        for gym in gp["gyms"]:
            assert gym["puzzle_type"] in valid, \
                f"{gym['id']} invalid puzzle: {gym['puzzle_type']}"

    def test_vermilion_trash_cans(self):
        gp = _load_json("gym_puzzles.json")
        verm = next(g for g in gp["gyms"] if g["id"] == "vermilion_gym")
        assert verm["puzzle_type"] == "trash_can_switches"
        assert verm["puzzle_config"]["trash_cans"] == 15
        assert verm["puzzle_config"]["switches"] == 2

    def test_saffron_teleport_pads(self):
        gp = _load_json("gym_puzzles.json")
        saf = next(g for g in gp["gyms"] if g["id"] == "saffron_gym")
        assert saf["puzzle_type"] == "teleport_pads"
        assert saf["puzzle_config"]["rooms"] == 9

    def test_cinnabar_quiz(self):
        gp = _load_json("gym_puzzles.json")
        cin = next(g for g in gp["gyms"] if g["id"] == "cinnabar_gym")
        assert cin["puzzle_type"] == "quiz_doors"
        assert cin["puzzle_config"]["questions"] == 6

    def test_trainer_count_increases(self):
        gp = _load_json("gym_puzzles.json")
        counts = [g["trainers_before_leader"] for g in gp["gyms"]]
        # Generally non-decreasing
        assert counts[-1] >= counts[0]

    def test_puzzle_type_count(self):
        gp = _load_json("gym_puzzles.json")
        assert len(gp["puzzle_types"]) == 7


# ──── Badge Effects Enhancements ───────────────────────────

class TestBadgeMechanics:
    def test_obedience_rules(self):
        bm = _load_json("badge_mechanics.json")
        ob = bm["obedience_rules"]
        assert ob["own_pokemon_always_obey"] is True
        assert ob["traded_pokemon_check"] is True

    def test_disobey_actions(self):
        bm = _load_json("badge_mechanics.json")
        actions = bm["obedience_rules"]["disobey_actions"]
        assert len(actions) == 4

    def test_hm_field_use_count(self):
        bm = _load_json("badge_mechanics.json")
        assert len(bm["hm_field_use"]) == 5

    def test_hm_field_use_have_badge(self):
        bm = _load_json("badge_mechanics.json")
        for move, data in bm["hm_field_use"].items():
            assert "badge_required" in data
            assert "animation" in data

    def test_cut_needs_cascade(self):
        bm = _load_json("badge_mechanics.json")
        assert bm["hm_field_use"]["Cut"]["badge_required"] == "cascade_badge"

    def test_surf_needs_soul(self):
        bm = _load_json("badge_mechanics.json")
        assert bm["hm_field_use"]["Surf"]["badge_required"] == "soul_badge"


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
