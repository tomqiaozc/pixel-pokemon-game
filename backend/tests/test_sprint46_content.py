"""Tests for Sprint 46: Route trainer teams, map tile properties, quest system.

These tests verify route/cave trainer rosters, terrain tile definitions,
and side quest/story quest configuration.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Route Trainer Teams ─────────────────────────────────────

class TestRouteTrainerTeams:
    def test_route_count(self):
        rt = _load_json("route_trainer_teams.json")
        assert len(rt) >= 20

    def test_all_have_route(self):
        rt = _load_json("route_trainer_teams.json")
        for entry in rt:
            assert "route" in entry
            assert "trainers" in entry

    def test_trainers_have_fields(self):
        rt = _load_json("route_trainer_teams.json")
        for entry in rt:
            for trainer in entry["trainers"]:
                assert "id" in trainer
                assert "name" in trainer
                assert "class" in trainer
                assert "team" in trainer
                assert len(trainer["team"]) >= 1

    def test_pokemon_have_fields(self):
        rt = _load_json("route_trainer_teams.json")
        for entry in rt:
            for trainer in entry["trainers"]:
                for pokemon in trainer["team"]:
                    assert "species" in pokemon
                    assert "level" in pokemon
                    assert "moves" in pokemon
                    assert len(pokemon["moves"]) >= 2

    def test_unique_trainer_ids(self):
        rt = _load_json("route_trainer_teams.json")
        all_ids = []
        for entry in rt:
            for trainer in entry["trainers"]:
                all_ids.append(trainer["id"])
        assert len(all_ids) == len(set(all_ids))

    def test_total_trainers(self):
        rt = _load_json("route_trainer_teams.json")
        total = sum(len(e["trainers"]) for e in rt)
        assert total >= 25

    def test_route1_no_trainers(self):
        rt = _load_json("route_trainer_teams.json")
        route1 = next(r for r in rt if r["route"] == "route_1")
        assert len(route1["trainers"]) == 0

    def test_route3_has_trainers(self):
        rt = _load_json("route_trainer_teams.json")
        route3 = next(r for r in rt if r["route"] == "route_3")
        assert len(route3["trainers"]) >= 2

    def test_diverse_classes(self):
        rt = _load_json("route_trainer_teams.json")
        classes = set()
        for entry in rt:
            for trainer in entry["trainers"]:
                classes.add(trainer["class"])
        assert len(classes) >= 8


# ──── Map Tile Properties ─────────────────────────────────────

class TestMapTileProperties:
    def test_tile_count(self):
        mt = _load_json("map_tile_properties.json")
        assert len(mt["tiles"]) == 18

    def test_all_tiles_have_fields(self):
        mt = _load_json("map_tile_properties.json")
        for tid, tile in mt["tiles"].items():
            assert "name" in tile, f"{tid} missing name"
            assert "walkable" in tile, f"{tid} missing walkable"
            assert "encounter_rate" in tile, f"{tid} missing encounter_rate"
            assert "description" in tile, f"{tid} missing description"

    def test_grass_walkable(self):
        mt = _load_json("map_tile_properties.json")
        assert mt["tiles"]["grass"]["walkable"] is True
        assert mt["tiles"]["tall_grass"]["walkable"] is True

    def test_wall_not_walkable(self):
        mt = _load_json("map_tile_properties.json")
        assert mt["tiles"]["wall"]["walkable"] is False

    def test_tall_grass_encounter_rate(self):
        mt = _load_json("map_tile_properties.json")
        assert mt["tiles"]["tall_grass"]["encounter_rate"] > 0

    def test_water_requires_surf(self):
        mt = _load_json("map_tile_properties.json")
        water = mt["tiles"]["water"]
        assert water["walkable"] is False
        assert water["surfable"] is True
        assert water["requires_hm"] == "Surf"

    def test_ledge_one_way(self):
        mt = _load_json("map_tile_properties.json")
        ledge = mt["tiles"]["ledge_down"]
        assert ledge["one_way"] is True
        assert ledge["direction"] == "down"

    def test_ice_sliding(self):
        mt = _load_json("map_tile_properties.json")
        assert mt["tiles"]["ice"]["sliding"] is True

    def test_dark_cave_requires_flash(self):
        mt = _load_json("map_tile_properties.json")
        dc = mt["tiles"]["dark_cave"]
        assert dc["dark"] is True
        assert dc["requires_hm"] == "Flash"

    def test_boulder_pushable(self):
        mt = _load_json("map_tile_properties.json")
        boulder = mt["tiles"]["boulder"]
        assert boulder["pushable"] is True
        assert boulder["requires_hm"] == "Strength"

    def test_cuttable_tree(self):
        mt = _load_json("map_tile_properties.json")
        tree = mt["tiles"]["cuttable_tree"]
        assert tree["cuttable"] is True
        assert tree["requires_hm"] == "Cut"

    def test_encounter_modifiers(self):
        mt = _load_json("map_tile_properties.json")
        mods = mt["encounter_modifiers"]
        assert mods["repel_active"] == 0
        assert mods["bike_riding"] < 1.0

    def test_movement_modifiers(self):
        mt = _load_json("map_tile_properties.json")
        mods = mt["movement_modifiers"]
        assert mods["bike"] > mods["walking"]
        assert mods["running_shoes"] > mods["walking"]

    def test_sand_slow_movement(self):
        mt = _load_json("map_tile_properties.json")
        assert mt["tiles"]["sand"]["movement_cost"] > 1


# ──── Quest System ────────────────────────────────────────────

class TestQuestSystem:
    def test_quest_count(self):
        quests = _load_json("quest_system.json")
        assert len(quests) == 15

    def test_all_have_required_fields(self):
        quests = _load_json("quest_system.json")
        for quest in quests:
            assert "id" in quest
            assert "name" in quest
            assert "type" in quest
            assert "description" in quest
            assert "objectives" in quest
            assert "rewards" in quest

    def test_quest_types_valid(self):
        quests = _load_json("quest_system.json")
        valid_types = {"story", "side"}
        for quest in quests:
            assert quest["type"] in valid_types, \
                f"{quest['id']} has invalid type: {quest['type']}"

    def test_unique_ids(self):
        quests = _load_json("quest_system.json")
        ids = [q["id"] for q in quests]
        assert len(ids) == len(set(ids))

    def test_objectives_have_fields(self):
        quests = _load_json("quest_system.json")
        for quest in quests:
            for obj in quest["objectives"]:
                assert "type" in obj
                assert "description" in obj

    def test_rewards_have_type(self):
        quests = _load_json("quest_system.json")
        for quest in quests:
            for reward in quest["rewards"]:
                assert "type" in reward

    def test_story_quests_exist(self):
        quests = _load_json("quest_system.json")
        story = [q for q in quests if q["type"] == "story"]
        assert len(story) >= 4

    def test_side_quests_exist(self):
        quests = _load_json("quest_system.json")
        side = [q for q in quests if q["type"] == "side"]
        assert len(side) >= 8

    def test_fishing_rod_quest_chain(self):
        quests = _load_json("quest_system.json")
        old = next(q for q in quests if q["id"] == "quest_old_rod")
        good = next(q for q in quests if q["id"] == "quest_good_rod")
        super_rod = next(q for q in quests if q["id"] == "quest_super_rod")
        assert "quest_old_rod" in good["prerequisites"]
        assert "quest_good_rod" in super_rod["prerequisites"]

    def test_pokedex_diploma_quest(self):
        quests = _load_json("quest_system.json")
        diploma = next(q for q in quests if q["id"] == "quest_pokedex_diploma")
        assert any(o["count"] == 151 for o in diploma["objectives"]
                   if o["type"] == "pokedex_count")

    def test_master_ball_quest(self):
        quests = _load_json("quest_system.json")
        mb = next(q for q in quests if q["id"] == "quest_master_ball")
        assert mb["type"] == "story"
        assert any(r["item"] == "Master Ball" for r in mb["rewards"]
                   if r["type"] == "item")

    def test_fossil_revival_repeatable(self):
        quests = _load_json("quest_system.json")
        fossil = next(q for q in quests if q["id"] == "quest_fossil_revival")
        assert fossil["repeatable"] is True

    def test_most_quests_not_repeatable(self):
        quests = _load_json("quest_system.json")
        repeatable = [q for q in quests if q.get("repeatable") is True]
        assert len(repeatable) <= 2


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
