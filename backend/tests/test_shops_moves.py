"""Tests for Sprint 28: Shop inventories and expanded move database.

These tests verify PokeMart shop inventories and the expanded move set.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Shop Inventories ──────────────────────────────────────

class TestShopInventories:
    EXPECTED_SHOPS = [
        "pallet_shop",
        "viridian_shop",
        "pewter_shop",
        "cerulean_shop",
        "vermilion_shop",
        "lavender_shop",
        "celadon_shop",
        "saffron_shop",
        "fuchsia_shop",
        "cinnabar_shop",
        "indigo_shop",
    ]

    @pytest.mark.parametrize("shop_id", EXPECTED_SHOPS)
    def test_shop_exists(self, shop_id):
        shops = _load_json("shops.json")
        assert shop_id in shops, f"Shop {shop_id} not found"
        assert "name" in shops[shop_id]
        assert len(shops[shop_id].get("items", [])) >= 2

    @pytest.mark.parametrize("shop_id", EXPECTED_SHOPS)
    def test_shop_items_valid(self, shop_id):
        shops = _load_json("shops.json")
        items = _load_json("items.json")
        item_ids = {i["id"] for i in items}
        for shop_item in shops[shop_id]["items"]:
            assert "item_id" in shop_item
            assert "stock" in shop_item
            assert shop_item["item_id"] in item_ids, (
                f"Shop {shop_id} references unknown item_id {shop_item['item_id']}"
            )

    def test_total_shops(self):
        shops = _load_json("shops.json")
        assert len(shops) == 11

    def test_celadon_has_most_items(self):
        shops = _load_json("shops.json")
        celadon = shops["celadon_shop"]
        assert len(celadon["items"]) >= 15, "Celadon Department Store should have largest inventory"

    def test_progressive_inventory(self):
        shops = _load_json("shops.json")
        pallet_count = len(shops["pallet_shop"]["items"])
        cerulean_count = len(shops["cerulean_shop"]["items"])
        celadon_count = len(shops["celadon_shop"]["items"])
        assert pallet_count < cerulean_count < celadon_count


# ──── Move Database ─────────────────────────────────────────

class TestMoveDatabase:
    def test_move_count(self):
        moves = _load_json("moves.json")
        assert len(moves) >= 119

    def test_all_moves_have_required_fields(self):
        moves = _load_json("moves.json")
        required_fields = ["name", "type", "category", "power", "accuracy", "pp"]
        for move_key, move in moves.items():
            for field in required_fields:
                assert field in move, f"Move {move_key} missing field {field}"

    def test_move_categories_valid(self):
        moves = _load_json("moves.json")
        valid_categories = {"physical", "special", "status"}
        for move_key, move in moves.items():
            assert move["category"] in valid_categories, (
                f"Move {move_key} has invalid category {move['category']}"
            )

    EXPECTED_NEW_MOVES = [
        "Mega Punch", "Mega Kick", "Swords Dance", "Body Slam",
        "Take Down", "Double-Edge", "Surf", "Fly", "Strength",
        "Dream Eater", "Rest", "Substitute", "Tri Attack",
        "Transform", "Struggle",
    ]

    @pytest.mark.parametrize("move_name", EXPECTED_NEW_MOVES)
    def test_new_move_exists(self, move_name):
        moves = _load_json("moves.json")
        assert move_name in moves, f"Move {move_name} not found"

    def test_hm_moves_exist(self):
        moves = _load_json("moves.json")
        hm_moves = ["Cut", "Fly", "Surf", "Strength", "Flash"]
        for hm in hm_moves:
            assert hm in moves, f"HM move {hm} not found"

    def test_status_moves_have_zero_power(self):
        moves = _load_json("moves.json")
        for move_key, move in moves.items():
            if move["category"] == "status":
                assert move["power"] == 0, f"Status move {move_key} should have 0 power"


# ──── Counts Unchanged ──────────────────────────────────────

class TestCountsUnchanged:
    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151

    def test_gyms_unchanged(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8

    def test_items_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 75
