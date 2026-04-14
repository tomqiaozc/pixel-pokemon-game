"""Tests for Sprint 40: Map events, warp points, field items.

These tests verify story event triggers, map door/cave connections,
and overworld item pickup locations.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Map Events ───────────────────────────────────────────────

class TestMapEvents:
    def test_event_count(self):
        events = _load_json("map_events.json")
        assert len(events) == 15

    def test_all_have_fields(self):
        events = _load_json("map_events.json")
        for event in events:
            assert "id" in event
            assert "type" in event
            assert "location" in event
            assert "trigger" in event
            assert "description" in event

    def test_event_types(self):
        events = _load_json("map_events.json")
        types = {e["type"] for e in events}
        assert "story" in types
        assert "legendary" in types
        assert "blocking" in types

    def test_legendary_events(self):
        events = _load_json("map_events.json")
        legendaries = [e for e in events if e["type"] == "legendary"]
        assert len(legendaries) == 4

    def test_team_rocket_events(self):
        events = _load_json("map_events.json")
        rocket = [e for e in events if "team_rocket" in e["id"]]
        assert len(rocket) >= 4

    def test_snorlax_blocking_events(self):
        events = _load_json("map_events.json")
        snorlax = [e for e in events if "snorlax" in e["id"]]
        assert len(snorlax) == 2

    def test_all_one_time(self):
        events = _load_json("map_events.json")
        for event in events:
            assert event["one_time"] is True

    def test_mewtwo_post_champion(self):
        events = _load_json("map_events.json")
        mewtwo = next(e for e in events if e["id"] == "legendary_mewtwo")
        assert mewtwo["required_progress"] == "become_champion"

    def test_unique_ids(self):
        events = _load_json("map_events.json")
        ids = [e["id"] for e in events]
        assert len(ids) == len(set(ids))


# ──── Warp Points ──────────────────────────────────────────────

class TestWarpPoints:
    def test_warp_count(self):
        warps = _load_json("warp_points.json")
        assert len(warps) == 23

    def test_all_have_fields(self):
        warps = _load_json("warp_points.json")
        for warp in warps:
            assert "from_map" in warp
            assert "from_x" in warp
            assert "from_y" in warp
            assert "to_map" in warp
            assert "to_x" in warp
            assert "to_y" in warp
            assert "type" in warp

    EXPECTED_TYPES = {"door", "cave", "ladder", "gate"}

    def test_warp_types(self):
        warps = _load_json("warp_points.json")
        types = {w["type"] for w in warps}
        assert types.issubset(self.EXPECTED_TYPES)

    def test_pallet_town_warps(self):
        warps = _load_json("warp_points.json")
        pallet = [w for w in warps if w["from_map"] == "pallet_town"]
        assert len(pallet) >= 3

    def test_gym_warps(self):
        warps = _load_json("warp_points.json")
        gyms = [w for w in warps if "gym" in w["to_map"]]
        assert len(gyms) >= 6

    def test_cave_warps(self):
        warps = _load_json("warp_points.json")
        caves = [w for w in warps if w["type"] in ("cave", "ladder")]
        assert len(caves) >= 3

    def test_coordinates_positive(self):
        warps = _load_json("warp_points.json")
        for warp in warps:
            assert warp["from_x"] >= 0
            assert warp["from_y"] >= 0
            assert warp["to_x"] >= 0
            assert warp["to_y"] >= 0


# ──── Field Items ──────────────────────────────────────────────

class TestFieldItems:
    def test_item_count(self):
        items = _load_json("field_items.json")
        assert len(items) == 20

    def test_all_have_fields(self):
        items = _load_json("field_items.json")
        for item in items:
            assert "id" in item
            assert "map_id" in item
            assert "x" in item
            assert "y" in item
            assert "item" in item
            assert "visible" in item

    def test_hidden_items_exist(self):
        items = _load_json("field_items.json")
        hidden = [i for i in items if not i["visible"]]
        assert len(hidden) >= 5

    def test_visible_items_exist(self):
        items = _load_json("field_items.json")
        visible = [i for i in items if i["visible"]]
        assert len(visible) >= 5

    def test_rare_candy_locations(self):
        items = _load_json("field_items.json")
        rare_candies = [i for i in items if i["item"] == "Rare Candy"]
        assert len(rare_candies) >= 2

    def test_no_respawn(self):
        items = _load_json("field_items.json")
        for item in items:
            assert item["respawn"] is False

    def test_unique_ids(self):
        items = _load_json("field_items.json")
        ids = [i["id"] for i in items]
        assert len(ids) == len(set(ids))

    def test_key_items_present(self):
        items = _load_json("field_items.json")
        item_names = {i["item"] for i in items}
        assert "Card Key" in item_names
        assert "Gold Teeth" in item_names


# ──── Counts ───────────────────────────────────────────────────

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
