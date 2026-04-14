"""Tests for Sprint 67: PC item storage, vending machine, pickup ability.

These tests verify Player's PC storage, Celadon vending machine,
and the Pickup ability item table.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── PC Item Storage ──────────────────────────────────────

class TestPCItemStorage:
    def test_max_unique_items(self):
        pc = _load_json("pc_item_storage.json")
        assert pc["storage"]["max_unique_items"] == 50

    def test_max_quantity(self):
        pc = _load_json("pc_item_storage.json")
        assert pc["storage"]["max_quantity_per_item"] == 999

    def test_operation_count(self):
        pc = _load_json("pc_item_storage.json")
        assert len(pc["operations"]) == 3

    def test_operations_have_fields(self):
        pc = _load_json("pc_item_storage.json")
        for op in pc["operations"]:
            assert "id" in op
            assert "name" in op

    def test_cannot_store_key_items(self):
        pc = _load_json("pc_item_storage.json")
        assert pc["restrictions"]["cannot_store_key_items"] is True

    def test_toss_confirm(self):
        pc = _load_json("pc_item_storage.json")
        assert pc["restrictions"]["toss_confirm_required"] is True

    def test_initial_potion(self):
        pc = _load_json("pc_item_storage.json")
        assert len(pc["initial_items"]) == 1
        assert pc["initial_items"][0]["item"] == "Potion"

    def test_dialogue_count(self):
        pc = _load_json("pc_item_storage.json")
        assert len(pc["dialogue"]) == 7


# ──── Vending Machine ─────────────────────────────────────

class TestVendingMachine:
    def test_location(self):
        vm = _load_json("vending_machine.json")
        assert vm["location"] == "celadon_dept_store_rooftop"

    def test_drink_count(self):
        vm = _load_json("vending_machine.json")
        drinks = vm["machines"][0]["items"]
        assert len(drinks) == 3

    def test_drinks_have_fields(self):
        vm = _load_json("vending_machine.json")
        for drink in vm["machines"][0]["items"]:
            assert "item" in drink
            assert "price" in drink
            assert "heal_amount" in drink

    def test_price_progression(self):
        vm = _load_json("vending_machine.json")
        drinks = vm["machines"][0]["items"]
        prices = [d["price"] for d in drinks]
        assert prices == sorted(prices)

    def test_heal_progression(self):
        vm = _load_json("vending_machine.json")
        drinks = vm["machines"][0]["items"]
        heals = [d["heal_amount"] for d in drinks]
        assert heals == sorted(heals)

    def test_guard_trades(self):
        vm = _load_json("vending_machine.json")
        trades = vm["guard_trade"]["trades"]
        assert len(trades) == 3
        for trade in trades:
            assert "give" in trade
            assert "receive" in trade
            assert trade["one_time"] is True

    def test_unlimited_stock(self):
        vm = _load_json("vending_machine.json")
        assert vm["mechanics"]["unlimited_stock"] is True


# ──── Pickup Ability ───────────────────────────────────────

class TestPickupAbility:
    def test_trigger(self):
        pa = _load_json("pickup_ability.json")
        assert pa["pickup_config"]["trigger"] == "after_battle"

    def test_chance(self):
        pa = _load_json("pickup_ability.json")
        assert pa["pickup_config"]["chance"] == 0.1

    def test_requires_no_held_item(self):
        pa = _load_json("pickup_ability.json")
        assert pa["pickup_config"]["requires_no_held_item"] is True

    def test_item_table_count(self):
        pa = _load_json("pickup_ability.json")
        assert len(pa["item_table"]) == 19

    def test_items_have_fields(self):
        pa = _load_json("pickup_ability.json")
        for entry in pa["item_table"]:
            assert "item" in entry
            assert "level_min" in entry
            assert "level_max" in entry
            assert "weight" in entry

    def test_level_ranges_valid(self):
        pa = _load_json("pickup_ability.json")
        for entry in pa["item_table"]:
            assert entry["level_min"] <= entry["level_max"], \
                f"{entry['item']} level_min > level_max"

    def test_weights_positive(self):
        pa = _load_json("pickup_ability.json")
        for entry in pa["item_table"]:
            assert entry["weight"] > 0

    def test_rare_candy_high_level(self):
        pa = _load_json("pickup_ability.json")
        rc = next(e for e in pa["item_table"] if e["item"] == "Rare Candy")
        assert rc["level_min"] >= 31

    def test_nugget_all_levels(self):
        pa = _load_json("pickup_ability.json")
        nugget = next(e for e in pa["item_table"] if e["item"] == "Nugget")
        assert nugget["level_min"] == 1
        assert nugget["level_max"] == 100


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
