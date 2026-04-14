"""Tests for Sprint 27: Item catalog expansion and missing encounter tables.

These tests verify evolution stones, battle items, vitamins, additional TMs,
healing items, and encounter tables for Routes 7 and 23.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Evolution Stones ──────────────────────────────────────

class TestEvolutionStones:
    EXPECTED_STONES = [
        "Fire Stone",
        "Water Stone",
        "Thunder Stone",
        "Leaf Stone",
        "Moon Stone",
    ]

    @pytest.mark.parametrize("stone_name", EXPECTED_STONES)
    def test_stone_exists(self, stone_name):
        items = _load_json("items.json")
        found = next((i for i in items if i["name"] == stone_name), None)
        assert found is not None, f"Evolution stone {stone_name} not found"
        assert found["category"] == "evolution"
        assert found["effect"]["type"] == "evolve"

    def test_stones_have_prices(self):
        items = _load_json("items.json")
        for stone_name in self.EXPECTED_STONES:
            stone = next(i for i in items if i["name"] == stone_name)
            assert "price" in stone
            assert "sell_price" in stone


# ──── Battle Items ──────────────────────────────────────────

class TestBattleItems:
    EXPECTED_ITEMS = [
        "X Attack",
        "X Defense",
        "X Speed",
        "X Special",
        "Guard Spec.",
        "Dire Hit",
    ]

    @pytest.mark.parametrize("item_name", EXPECTED_ITEMS)
    def test_item_exists(self, item_name):
        items = _load_json("items.json")
        found = next((i for i in items if i["name"] == item_name), None)
        assert found is not None, f"Battle item {item_name} not found"
        assert found["category"] == "battle"


# ──── Vitamins ──────────────────────────────────────────────

class TestVitamins:
    EXPECTED_VITAMINS = [
        ("HP Up", "vitamin"),
        ("Protein", "vitamin"),
        ("Iron", "vitamin"),
        ("Calcium", "vitamin"),
        ("Carbos", "vitamin"),
        ("Rare Candy", "medicine"),
        ("PP Up", "medicine"),
    ]

    @pytest.mark.parametrize("vitamin_name,category", EXPECTED_VITAMINS)
    def test_vitamin_exists(self, vitamin_name, category):
        items = _load_json("items.json")
        found = next((i for i in items if i["name"] == vitamin_name), None)
        assert found is not None, f"Vitamin {vitamin_name} not found"
        assert found["category"] == category

    def test_rare_candy_levels_up(self):
        items = _load_json("items.json")
        rc = next(i for i in items if i["name"] == "Rare Candy")
        assert rc["effect"]["type"] == "level_up"


# ──── Healing Items ─────────────────────────────────────────

class TestHealingItems:
    EXPECTED_ITEMS = [
        ("Max Potion", "potion"),
        ("Full Restore", "potion"),
        ("Revive", "potion"),
        ("Max Revive", "medicine"),
        ("Elixir", "medicine"),
        ("Max Elixir", "medicine"),
        ("Ether", "medicine"),
    ]

    @pytest.mark.parametrize("item_name,category", EXPECTED_ITEMS)
    def test_item_exists(self, item_name, category):
        items = _load_json("items.json")
        found = next((i for i in items if i["name"] == item_name), None)
        assert found is not None, f"Healing item {item_name} not found"
        assert found["category"] == category


# ──── Additional TMs ────────────────────────────────────────

class TestAdditionalTMs:
    EXPECTED_TMS = [
        "TM01 Mega Punch",
        "TM02 Razor Wind",
        "TM03 Swords Dance",
        "TM05 Mega Kick",
        "TM08 Body Slam",
        "TM09 Take Down",
        "TM10 Double-Edge",
        "TM11 Bubble Beam",
        "TM12 Water Gun",
    ]

    @pytest.mark.parametrize("tm_name", EXPECTED_TMS)
    def test_tm_exists(self, tm_name):
        items = _load_json("items.json")
        found = next((i for i in items if i["name"] == tm_name), None)
        assert found is not None, f"TM {tm_name} not found"
        assert found["category"] == "tm"
        assert found["effect"]["type"] == "teach_move"


# ──── Encounter Tables ──────────────────────────────────────

class TestNewEncounterTables:
    def test_route_7_encounters(self):
        tables = _load_json("encounter_tables.json")
        assert "route_7" in tables
        assert tables["route_7"]["encounter_type"] == "grass"
        assert len(tables["route_7"]["encounters"]) >= 4

    def test_route_23_encounters(self):
        tables = _load_json("encounter_tables.json")
        assert "route_23" in tables
        assert tables["route_23"]["encounter_type"] == "grass"
        assert len(tables["route_23"]["encounters"]) >= 4

    def test_total_encounter_tables(self):
        tables = _load_json("encounter_tables.json")
        assert len(tables) == 52


# ──── Total Counts ──────────────────────────────────────────

class TestTotalCounts:
    def test_total_items(self):
        items = _load_json("items.json")
        assert len(items) == 93

    def test_no_duplicate_item_ids(self):
        items = _load_json("items.json")
        ids = [i["id"] for i in items]
        assert len(ids) == len(set(ids)), "Duplicate item IDs found"

    def test_all_items_have_required_fields(self):
        items = _load_json("items.json")
        for item in items:
            assert "id" in item
            assert "name" in item
            assert "category" in item
            assert "price" in item
            assert "sell_price" in item
            assert "effect" in item

    def test_counts_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132
        species = _load_json("pokemon_species.json")
        assert len(species) == 151
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8
