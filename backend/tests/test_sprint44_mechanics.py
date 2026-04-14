"""Tests for Sprint 44: Move priority, berry growth, evolution stone locations.

These tests verify move priority brackets, berry planting/harvesting mechanics,
and evolution stone acquisition locations.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Move Priority ──────────────────────────────────────────

class TestMovePriority:
    def test_has_moves(self):
        mp = _load_json("move_priority.json")
        assert len(mp["moves"]) >= 70

    def test_has_priority_brackets(self):
        mp = _load_json("move_priority.json")
        assert len(mp["priority_brackets"]) >= 5

    def test_all_moves_have_priority(self):
        mp = _load_json("move_priority.json")
        for move, data in mp["moves"].items():
            assert "priority" in data, f"{move} missing priority"

    def test_quick_attack_priority(self):
        mp = _load_json("move_priority.json")
        assert mp["moves"]["Quick Attack"]["priority"] == 1

    def test_normal_moves_zero_priority(self):
        mp = _load_json("move_priority.json")
        for move in ["Tackle", "Scratch", "Flamethrower", "Surf", "Thunderbolt"]:
            assert mp["moves"][move]["priority"] == 0

    def test_negative_priority_moves(self):
        mp = _load_json("move_priority.json")
        neg = {m: d for m, d in mp["moves"].items() if d["priority"] < 0}
        assert len(neg) >= 5

    def test_positive_priority_moves(self):
        mp = _load_json("move_priority.json")
        pos = {m: d for m, d in mp["moves"].items() if d["priority"] > 0}
        assert len(pos) >= 3

    def test_counter_low_priority(self):
        mp = _load_json("move_priority.json")
        assert mp["moves"]["Counter"]["priority"] <= -3

    def test_whirlwind_negative(self):
        mp = _load_json("move_priority.json")
        assert mp["moves"]["Whirlwind"]["priority"] < 0

    def test_default_priority(self):
        mp = _load_json("move_priority.json")
        assert mp["default_priority"] == 0

    def test_rules_present(self):
        mp = _load_json("move_priority.json")
        rules = mp["rules"]
        assert rules["same_priority_uses_speed"] is True
        assert rules["speed_tie_random"] is True

    def test_gen1_moves_in_moves_json(self):
        mp = _load_json("move_priority.json")
        moves = _load_json("moves.json")
        gen1_priority = [m for m in mp["moves"]
                         if m in moves]
        assert len(gen1_priority) >= 60


# ──── Berry Growth ────────────────────────────────────────────

class TestBerryGrowth:
    def test_has_garden_locations(self):
        bg = _load_json("berry_growth.json")
        assert len(bg["garden_locations"]) >= 4

    def test_total_plots(self):
        bg = _load_json("berry_growth.json")
        total = sum(g["plots"] for g in bg["garden_locations"])
        assert total == bg["total_plots"]
        assert total >= 20

    def test_growth_stages(self):
        bg = _load_json("berry_growth.json")
        assert len(bg["growth_stages"]) == 5
        stages = [s["stage"] for s in bg["growth_stages"]]
        assert stages == [1, 2, 3, 4, 5]

    def test_final_stage_is_ready(self):
        bg = _load_json("berry_growth.json")
        assert bg["growth_stages"][-1]["name"] == "Ready"

    def test_berry_count(self):
        bg = _load_json("berry_growth.json")
        assert len(bg["berries"]) == 10

    def test_all_berries_have_fields(self):
        bg = _load_json("berry_growth.json")
        for bid, berry in bg["berries"].items():
            assert "name" in berry, f"{bid} missing name"
            assert "growth_time_hours" in berry, f"{bid} missing growth_time_hours"
            assert "base_yield" in berry, f"{bid} missing base_yield"
            assert "max_yield" in berry, f"{bid} missing max_yield"
            assert berry["max_yield"] >= berry["base_yield"]

    def test_growth_times_positive(self):
        bg = _load_json("berry_growth.json")
        for bid, berry in bg["berries"].items():
            assert berry["growth_time_hours"] > 0

    def test_stage_duration_consistent(self):
        bg = _load_json("berry_growth.json")
        for bid, berry in bg["berries"].items():
            expected = berry["growth_time_hours"] / 5
            assert abs(berry["stage_duration_hours"] - expected) < 0.01, \
                f"{bid} stage duration inconsistent"

    def test_watering_mechanics(self):
        bg = _load_json("berry_growth.json")
        water = bg["watering"]
        assert water["max_water_level"] == 3
        assert water["dry_yield_penalty"] == 0.5

    def test_mulch_types(self):
        bg = _load_json("berry_growth.json")
        mulch = bg["mechanics"]["mulch_types"]
        assert len(mulch) == 4
        assert "growth_mulch" in mulch
        assert "damp_mulch" in mulch

    def test_wilt_mechanic(self):
        bg = _load_json("berry_growth.json")
        assert bg["mechanics"]["wilt_after_ready_hours"] == 24

    def test_berries_match_items(self):
        bg = _load_json("berry_growth.json")
        items = _load_json("items.json")
        item_names = {i["name"] for i in items}
        for bid, berry in bg["berries"].items():
            assert berry["name"] in item_names, \
                f"{berry['name']} not found in items.json"

    def test_garden_fields(self):
        bg = _load_json("berry_growth.json")
        for garden in bg["garden_locations"]:
            assert "id" in garden
            assert "name" in garden
            assert "plots" in garden
            assert garden["plots"] > 0


# ──── Evolution Stone Locations ───────────────────────────────

class TestEvolutionStoneLocations:
    def test_stone_count(self):
        stones = _load_json("evolution_stone_locations.json")
        assert len(stones) == 5

    EXPECTED_STONES = {"Fire Stone", "Water Stone", "Thunder Stone", "Leaf Stone", "Moon Stone"}

    def test_all_gen1_stones_present(self):
        stones = _load_json("evolution_stone_locations.json")
        stone_names = {s["stone"] for s in stones}
        assert stone_names == self.EXPECTED_STONES

    def test_all_have_sources(self):
        stones = _load_json("evolution_stone_locations.json")
        for stone in stones:
            assert "sources" in stone
            assert len(stone["sources"]) >= 2

    def test_source_types_valid(self):
        stones = _load_json("evolution_stone_locations.json")
        valid_types = {"shop", "field_item", "gift"}
        for stone in stones:
            for source in stone["sources"]:
                assert source["type"] in valid_types, \
                    f"{stone['stone']} has invalid source type: {source['type']}"

    def test_shop_sources_have_price(self):
        stones = _load_json("evolution_stone_locations.json")
        for stone in stones:
            for source in stone["sources"]:
                if source["type"] == "shop":
                    assert "price" in source
                    assert source["price"] > 0

    def test_field_items_have_location(self):
        stones = _load_json("evolution_stone_locations.json")
        for stone in stones:
            for source in stone["sources"]:
                if source["type"] == "field_item":
                    assert "location" in source

    def test_celadon_sells_four_stones(self):
        stones = _load_json("evolution_stone_locations.json")
        celadon_stones = []
        for stone in stones:
            for source in stone["sources"]:
                if source["type"] == "shop" and source.get("location") == "celadon_city":
                    celadon_stones.append(stone["stone"])
        assert len(celadon_stones) == 4

    def test_moon_stone_not_in_shops(self):
        stones = _load_json("evolution_stone_locations.json")
        moon = next(s for s in stones if s["stone"] == "Moon Stone")
        shop_sources = [src for src in moon["sources"] if src["type"] == "shop"]
        assert len(shop_sources) == 0

    def test_moon_stone_mt_moon(self):
        stones = _load_json("evolution_stone_locations.json")
        moon = next(s for s in stones if s["stone"] == "Moon Stone")
        mt_moon = [src for src in moon["sources"]
                   if src.get("location") == "mt_moon"]
        assert len(mt_moon) >= 2

    def test_hidden_items_exist(self):
        stones = _load_json("evolution_stone_locations.json")
        hidden = []
        for stone in stones:
            for source in stone["sources"]:
                if source.get("hidden") is True:
                    hidden.append(stone["stone"])
        assert len(hidden) >= 4


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
