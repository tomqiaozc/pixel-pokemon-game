"""Tests for Sprint 43: AI strategies, shop inventories, move animations.

These tests verify trainer AI battle behavior data, Poke Mart shop
inventories, and move animation/visual display properties.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── AI Strategies ───────────────────────────────────────────

class TestAIStrategies:
    def test_strategy_count(self):
        ai = _load_json("ai_strategies.json")
        assert len(ai) == 8

    def test_all_have_required_fields(self):
        ai = _load_json("ai_strategies.json")
        for sid, data in ai.items():
            assert "name" in data, f"{sid} missing name"
            assert "description" in data, f"{sid} missing description"
            assert "difficulty" in data, f"{sid} missing difficulty"
            assert "used_by" in data, f"{sid} missing used_by"
            assert "behavior" in data, f"{sid} missing behavior"

    VALID_DIFFICULTIES = {"easy", "medium", "hard", "very_hard"}

    def test_difficulties_valid(self):
        ai = _load_json("ai_strategies.json")
        for sid, data in ai.items():
            assert data["difficulty"] in self.VALID_DIFFICULTIES, \
                f"{sid} has invalid difficulty: {data['difficulty']}"

    def test_all_behaviors_have_move_selection(self):
        ai = _load_json("ai_strategies.json")
        for sid, data in ai.items():
            assert "move_selection" in data["behavior"], \
                f"{sid} missing move_selection"

    def test_random_strategy(self):
        ai = _load_json("ai_strategies.json")
        rand = ai["random"]
        assert rand["difficulty"] == "easy"
        assert rand["behavior"]["move_selection"] == "random"
        assert "wild_pokemon" in rand["used_by"]

    def test_gym_leader_strategy(self):
        ai = _load_json("ai_strategies.json")
        gl = ai["gym_leader"]
        assert gl["difficulty"] == "hard"
        assert gl["behavior"]["lead_with_setup"] is True
        assert gl["behavior"]["item_usage"] is True

    def test_champion_strategy(self):
        ai = _load_json("ai_strategies.json")
        ch = ai["champion"]
        assert ch["difficulty"] == "very_hard"
        assert ch["behavior"]["predict_player_moves"] is True

    def test_elite_four_strategy(self):
        ai = _load_json("ai_strategies.json")
        e4 = ai["elite_four"]
        assert e4["difficulty"] == "very_hard"
        assert e4["behavior"]["switch_on_disadvantage"] is True

    def test_smart_has_weights(self):
        ai = _load_json("ai_strategies.json")
        smart = ai["smart"]
        weights = smart["behavior"]["weights"]
        assert "damage" in weights
        assert "type_advantage" in weights
        assert "accuracy" in weights

    def test_difficulty_progression(self):
        ai = _load_json("ai_strategies.json")
        diff_order = {"easy": 0, "medium": 1, "hard": 2, "very_hard": 3}
        assert diff_order[ai["random"]["difficulty"]] <= diff_order[ai["basic"]["difficulty"]]
        assert diff_order[ai["basic"]["difficulty"]] <= diff_order[ai["smart"]["difficulty"]]
        assert diff_order[ai["smart"]["difficulty"]] <= diff_order[ai["champion"]["difficulty"]]


# ──── Shop Inventories ────────────────────────────────────────

class TestShopInventories:
    def test_shop_count(self):
        shops = _load_json("shop_inventories.json")
        assert len(shops) == 12

    def test_all_have_required_fields(self):
        shops = _load_json("shop_inventories.json")
        for shop in shops:
            assert "id" in shop, "shop missing id"
            assert "name" in shop, "shop missing name"
            assert "location" in shop, "shop missing location"
            assert "items" in shop, "shop missing items"
            assert len(shop["items"]) >= 1

    def test_all_items_have_price(self):
        shops = _load_json("shop_inventories.json")
        for shop in shops:
            for item in shop["items"]:
                assert "item" in item, f"item in {shop['id']} missing name"
                assert "price" in item, f"item in {shop['id']} missing price"
                assert item["price"] > 0

    def test_unique_ids(self):
        shops = _load_json("shop_inventories.json")
        ids = [s["id"] for s in shops]
        assert len(ids) == len(set(ids))

    def test_viridian_mart_basic_items(self):
        shops = _load_json("shop_inventories.json")
        viridian = next(s for s in shops if s["id"] == "viridian_mart")
        item_names = {i["item"] for i in viridian["items"]}
        assert "Poke Ball" in item_names
        assert "Potion" in item_names

    def test_indigo_mart_endgame_items(self):
        shops = _load_json("shop_inventories.json")
        indigo = next(s for s in shops if s["id"] == "indigo_mart")
        item_names = {i["item"] for i in indigo["items"]}
        assert "Ultra Ball" in item_names
        assert "Full Restore" in item_names

    def test_celadon_has_evolution_stones(self):
        shops = _load_json("shop_inventories.json")
        celadon_4f = next(s for s in shops if s["id"] == "celadon_mart_4f")
        item_names = {i["item"] for i in celadon_4f["items"]}
        assert "Fire Stone" in item_names
        assert "Water Stone" in item_names
        assert "Thunder Stone" in item_names
        assert "Leaf Stone" in item_names

    def test_celadon_multiple_floors(self):
        shops = _load_json("shop_inventories.json")
        celadon_shops = [s for s in shops if s["location"] == "celadon_city"]
        assert len(celadon_shops) >= 3

    def test_prices_increase_with_progression(self):
        shops = _load_json("shop_inventories.json")
        viridian = next(s for s in shops if s["id"] == "viridian_mart")
        indigo = next(s for s in shops if s["id"] == "indigo_mart")
        v_max = max(i["price"] for i in viridian["items"])
        i_max = max(i["price"] for i in indigo["items"])
        assert i_max > v_max


# ──── Move Animations ────────────────────────────────────────

class TestMoveAnimations:
    def test_animation_count(self):
        anims = _load_json("move_animations.json")
        assert len(anims) == 64

    def test_all_have_required_fields(self):
        anims = _load_json("move_animations.json")
        for move, data in anims.items():
            assert "color" in data, f"{move} missing color"
            assert "style" in data, f"{move} missing style"
            assert "particles" in data, f"{move} missing particles"
            assert "duration_ms" in data, f"{move} missing duration_ms"

    def test_colors_are_hex(self):
        anims = _load_json("move_animations.json")
        import re
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for move, data in anims.items():
            assert hex_pattern.match(data["color"]), \
                f"{move} color {data['color']} is not valid hex"

    def test_durations_positive(self):
        anims = _load_json("move_animations.json")
        for move, data in anims.items():
            assert data["duration_ms"] > 0, f"{move} has non-positive duration"

    def test_fire_moves_orange(self):
        anims = _load_json("move_animations.json")
        fire_color = "#F08030"
        assert anims["Flamethrower"]["color"] == fire_color
        assert anims["Fire Blast"]["color"] == fire_color
        assert anims["Ember"]["color"] == fire_color

    def test_water_moves_blue(self):
        anims = _load_json("move_animations.json")
        water_color = "#6890F0"
        assert anims["Water Gun"]["color"] == water_color
        assert anims["Surf"]["color"] == water_color
        assert anims["Hydro Pump"]["color"] == water_color

    def test_electric_moves_yellow(self):
        anims = _load_json("move_animations.json")
        elec_color = "#F8D030"
        assert anims["Thunderbolt"]["color"] == elec_color
        assert anims["Thunder"]["color"] == elec_color

    def test_beam_moves_longer(self):
        anims = _load_json("move_animations.json")
        beam_moves = {m: d for m, d in anims.items() if d["style"] == "beam"}
        for move, data in beam_moves.items():
            assert data["duration_ms"] >= 600, \
                f"{move} beam duration too short"

    def test_self_buff_moves(self):
        anims = _load_json("move_animations.json")
        buffs = {m: d for m, d in anims.items() if d["style"] == "self_buff"}
        assert len(buffs) >= 5
        for move, data in buffs.items():
            assert data["particles"] != "none"

    def test_explosion_long_duration(self):
        anims = _load_json("move_animations.json")
        assert anims["Self Destruct"]["duration_ms"] >= 1000
        assert anims["Explosion"]["duration_ms"] >= 1000

    def test_moves_exist_in_moves_json(self):
        anims = _load_json("move_animations.json")
        moves = _load_json("moves.json")
        for move_name in anims:
            assert move_name in moves, f"{move_name} not found in moves.json"


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
