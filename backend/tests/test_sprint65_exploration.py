"""Tests for Sprint 65: Fishing system, bike mechanics, repel system.

These tests verify fishing rod encounters, bicycle configuration,
and repel item mechanics.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Fishing System ───────────────────────────────────────

class TestFishingSystem:
    def test_rod_count(self):
        fs = _load_json("fishing_system.json")
        assert len(fs["rods"]) == 3

    def test_rods_have_fields(self):
        fs = _load_json("fishing_system.json")
        for rod in fs["rods"]:
            assert "id" in rod
            assert "name" in rod
            assert "power" in rod
            assert "bite_chance" in rod
            assert "encounters" in rod

    def test_rod_power_progression(self):
        fs = _load_json("fishing_system.json")
        rods = sorted(fs["rods"], key=lambda r: r["power"])
        assert rods[0]["id"] == "old_rod"
        assert rods[1]["id"] == "good_rod"
        assert rods[2]["id"] == "super_rod"

    def test_old_rod_magikarp_only(self):
        fs = _load_json("fishing_system.json")
        old = next(r for r in fs["rods"] if r["id"] == "old_rod")
        assert len(old["encounters"]) == 1
        assert old["encounters"][0]["pokemon"] == "Magikarp"

    def test_super_rod_most_encounters(self):
        fs = _load_json("fishing_system.json")
        super_rod = next(r for r in fs["rods"] if r["id"] == "super_rod")
        old_rod = next(r for r in fs["rods"] if r["id"] == "old_rod")
        assert len(super_rod["encounters"]) > len(old_rod["encounters"])

    def test_bite_chance_progression(self):
        fs = _load_json("fishing_system.json")
        old = next(r for r in fs["rods"] if r["id"] == "old_rod")
        good = next(r for r in fs["rods"] if r["id"] == "good_rod")
        super_r = next(r for r in fs["rods"] if r["id"] == "super_rod")
        assert old["bite_chance"] <= good["bite_chance"] <= super_r["bite_chance"]

    def test_fishing_spots(self):
        fs = _load_json("fishing_system.json")
        assert len(fs["fishing_spots"]) == 12
        for spot in fs["fishing_spots"]:
            assert spot["has_water"] is True

    def test_dratini_in_super_rod(self):
        fs = _load_json("fishing_system.json")
        super_rod = next(r for r in fs["rods"] if r["id"] == "super_rod")
        pokemon = {e["pokemon"] for e in super_rod["encounters"]}
        assert "Dratini" in pokemon

    def test_mechanics(self):
        fs = _load_json("fishing_system.json")
        m = fs["mechanics"]
        assert m["face_water_required"] is True
        assert m["animation_ms"] > 0


# ──── Bike Mechanics ───────────────────────────────────────

class TestBikeMechanics:
    def test_obtain_location(self):
        bm = _load_json("bike_mechanics.json")
        assert bm["bicycle"]["obtain_location"] == "cerulean_city"

    def test_voucher_source(self):
        bm = _load_json("bike_mechanics.json")
        assert bm["bicycle"]["voucher_location"] == "vermilion_city"

    def test_speed_progression(self):
        bm = _load_json("bike_mechanics.json")
        s = bm["speed"]
        assert s["walk_speed"] < s["run_speed"] < s["bike_speed"]

    def test_restrictions(self):
        bm = _load_json("bike_mechanics.json")
        r = bm["restrictions"]
        assert r["cannot_use_indoors"] is True
        assert r["cannot_use_on_water"] is True

    def test_blocked_maps(self):
        bm = _load_json("bike_mechanics.json")
        blocked = bm["restrictions"]["blocked_maps"]
        assert len(blocked) >= 3

    def test_cycling_road(self):
        bm = _load_json("bike_mechanics.json")
        cr = bm["cycling_road"]
        assert cr["location"] == "route_17"
        assert cr["bike_required"] is True
        assert cr["auto_move"] is True

    def test_cycling_road_connects(self):
        bm = _load_json("bike_mechanics.json")
        connects = bm["cycling_road"]["connects"]
        assert "celadon_city" in connects
        assert "fuchsia_city" in connects

    def test_slope_sections(self):
        bm = _load_json("bike_mechanics.json")
        slopes = bm["cycling_road"]["slope_sections"]
        assert len(slopes) == 3
        for s in slopes:
            assert "speed_boost" in s

    def test_animation(self):
        bm = _load_json("bike_mechanics.json")
        a = bm["animation"]
        assert len(a["directions"]) == 4


# ──── Repel System ─────────────────────────────────────────

class TestRepelSystem:
    def test_repel_type_count(self):
        rs = _load_json("repel_system.json")
        assert len(rs["repel_types"]) == 3

    def test_repel_types_have_fields(self):
        rs = _load_json("repel_system.json")
        for rt in rs["repel_types"]:
            assert "id" in rt
            assert "name" in rt
            assert "steps" in rt
            assert "cost" in rt

    def test_step_progression(self):
        rs = _load_json("repel_system.json")
        types = sorted(rs["repel_types"], key=lambda r: r["steps"])
        assert types[0]["id"] == "repel"
        assert types[1]["id"] == "super_repel"
        assert types[2]["id"] == "max_repel"

    def test_cost_progression(self):
        rs = _load_json("repel_system.json")
        types = sorted(rs["repel_types"], key=lambda r: r["cost"])
        assert types[0]["cost"] < types[1]["cost"] < types[2]["cost"]

    def test_level_based_mechanics(self):
        rs = _load_json("repel_system.json")
        m = rs["mechanics"]
        assert m["level_based"] is True
        assert m["compare_to"] == "first_party_pokemon"
        assert m["blocks_lower_level"] is True

    def test_no_stacking(self):
        rs = _load_json("repel_system.json")
        assert rs["mechanics"]["stacking"] is False

    def test_messages(self):
        rs = _load_json("repel_system.json")
        msgs = rs["messages"]
        assert len(msgs) == 5
        assert "{repel}" in msgs["use"]

    def test_prompt_on_expire(self):
        rs = _load_json("repel_system.json")
        p = rs["prompt_on_expire"]
        assert p["enabled"] is True


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
