"""Tests for Sprint 69: NPC gift Pokemon, hidden items, in-game trades.

These tests verify NPC-given Pokemon, hidden item map locations,
and in-game trade NPC details.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── NPC Gift Pokemon ─────────────────────────────────────

class TestNPCGiftPokemon:
    def test_gift_count(self):
        gp = _load_json("npc_gift_pokemon.json")
        assert len(gp["gifts"]) == 8

    def test_gifts_have_fields(self):
        gp = _load_json("npc_gift_pokemon.json")
        for gift in gp["gifts"]:
            assert "id" in gift
            assert "pokemon" in gift
            assert "level" in gift
            assert "location" in gift
            assert "npc" in gift

    def test_unique_gift_ids(self):
        gp = _load_json("npc_gift_pokemon.json")
        ids = [g["id"] for g in gp["gifts"]]
        assert len(ids) == len(set(ids))

    def test_all_one_time(self):
        gp = _load_json("npc_gift_pokemon.json")
        for gift in gp["gifts"]:
            assert gift["one_time"] is True

    def test_three_starters(self):
        gp = _load_json("npc_gift_pokemon.json")
        starters = [g for g in gp["gifts"] if g.get("choice_group") == "starter"]
        assert len(starters) == 3
        species = {s["pokemon"] for s in starters}
        assert "Bulbasaur" in species
        assert "Charmander" in species
        assert "Squirtle" in species

    def test_starters_level_5(self):
        gp = _load_json("npc_gift_pokemon.json")
        starters = [g for g in gp["gifts"] if g.get("choice_group") == "starter"]
        for s in starters:
            assert s["level"] == 5

    def test_eevee_gift(self):
        gp = _load_json("npc_gift_pokemon.json")
        eevee = next(g for g in gp["gifts"] if g["pokemon"] == "Eevee")
        assert eevee["location"] == "celadon_mansion"

    def test_fighting_choice(self):
        gp = _load_json("npc_gift_pokemon.json")
        fighters = [g for g in gp["gifts"] if g.get("choice_group") == "fighting"]
        assert len(fighters) == 2
        species = {f["pokemon"] for f in fighters}
        assert "Hitmonlee" in species
        assert "Hitmonchan" in species

    def test_choice_groups(self):
        gp = _load_json("npc_gift_pokemon.json")
        groups = gp["choice_groups"]
        assert groups["starter"]["pick_one"] is True
        assert groups["fighting"]["pick_one"] is True

    def test_lapras_silph(self):
        gp = _load_json("npc_gift_pokemon.json")
        lapras = next(g for g in gp["gifts"] if g["pokemon"] == "Lapras")
        assert lapras["location"] == "silph_co"


# ──── Hidden Items ─────────────────────────────────────────

class TestHiddenItems:
    def test_hidden_item_count(self):
        hi = _load_json("hidden_items.json")
        assert len(hi["hidden_items"]) == 20

    def test_items_have_fields(self):
        hi = _load_json("hidden_items.json")
        for item in hi["hidden_items"]:
            assert "id" in item
            assert "item" in item
            assert "location" in item
            assert "x" in item
            assert "y" in item

    def test_unique_hidden_ids(self):
        hi = _load_json("hidden_items.json")
        ids = [i["id"] for i in hi["hidden_items"]]
        assert len(ids) == len(set(ids))

    def test_none_respawn(self):
        hi = _load_json("hidden_items.json")
        for item in hi["hidden_items"]:
            assert item["respawns"] is False

    def test_rare_candies(self):
        hi = _load_json("hidden_items.json")
        rcs = [i for i in hi["hidden_items"] if i["item"] == "Rare Candy"]
        assert len(rcs) >= 3

    def test_itemfinder_config(self):
        hi = _load_json("hidden_items.json")
        finder = hi["itemfinder"]
        assert finder["obtain_location"] == "route_11"
        assert finder["range_tiles"] > 0
        assert finder["beep_when_near"] is True


# ──── In-Game Trade Enhancements ──────────────────────────

class TestInGameTradeDetails:
    def test_trade_count(self):
        trades = _load_json("ingame_trades.json")
        assert len(trades) == 8

    def test_all_have_dialogue(self):
        trades = _load_json("ingame_trades.json")
        for trade in trades:
            assert "dialogue" in trade
            assert len(trade["dialogue"]) > 0

    def test_all_have_levels(self):
        trades = _load_json("ingame_trades.json")
        for trade in trades:
            assert "offered_level" in trade
            assert trade["offered_level"] > 0


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
