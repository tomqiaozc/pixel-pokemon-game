"""Tests for Sprint 48: Game Corner, learnset validation, trainer dialogues.

These tests verify Game Corner configuration, species learnset cross-reference
data, and route trainer pre/post battle dialogues.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Game Corner ─────────────────────────────────────────────

class TestGameCorner:
    def test_location(self):
        gc = _load_json("game_corner.json")
        assert gc["location"] == "celadon_city"

    def test_coin_purchase(self):
        gc = _load_json("game_corner.json")
        assert "50_coins" in gc["coin_purchase"]
        assert "500_coins" in gc["coin_purchase"]
        assert gc["coin_purchase"]["50_coins"] > 0

    def test_slot_machines(self):
        gc = _load_json("game_corner.json")
        slots = gc["slot_machines"]
        assert slots["count"] >= 10
        assert slots["cost_per_play"] > 0
        assert len(slots["symbols"]) >= 5

    def test_slot_payouts(self):
        gc = _load_json("game_corner.json")
        payouts = gc["slot_machines"]["payouts"]
        assert payouts["777"] > payouts["BAR_BAR_BAR"]
        assert payouts["BAR_BAR_BAR"] > payouts["cherry_cherry_cherry"]

    def test_pokemon_prizes(self):
        gc = _load_json("game_corner.json")
        pokemon = gc["prizes"]["pokemon"]
        assert len(pokemon) >= 5
        for p in pokemon:
            assert "species" in p
            assert "cost_coins" in p
            assert "level" in p

    def test_porygon_most_expensive(self):
        gc = _load_json("game_corner.json")
        pokemon = gc["prizes"]["pokemon"]
        porygon = next(p for p in pokemon if p["species"] == "Porygon")
        for p in pokemon:
            assert p["cost_coins"] <= porygon["cost_coins"]

    def test_dratini_available(self):
        gc = _load_json("game_corner.json")
        pokemon = gc["prizes"]["pokemon"]
        dratini = next(p for p in pokemon if p["species"] == "Dratini")
        assert dratini["cost_coins"] > 0

    def test_tm_prizes(self):
        gc = _load_json("game_corner.json")
        tms = gc["prizes"]["tms"]
        assert len(tms) >= 3
        for tm in tms:
            assert "item" in tm
            assert "move" in tm
            assert "cost_coins" in tm

    def test_item_prizes(self):
        gc = _load_json("game_corner.json")
        items = gc["prizes"]["items"]
        assert len(items) >= 3

    def test_rocket_hideout(self):
        gc = _load_json("game_corner.json")
        rh = gc["team_rocket_hideout"]
        assert rh["floors"] == 4
        assert rh["boss"] == "giovanni"


# ──── Learnset Validation ────────────────────────────────────

class TestLearnsetValidation:
    def test_has_description(self):
        lv = _load_json("learnset_validation.json")
        assert "description" in lv

    def test_total_species(self):
        lv = _load_json("learnset_validation.json")
        assert lv["total_species"] == 151

    def test_total_moves(self):
        lv = _load_json("learnset_validation.json")
        assert lv["total_moves"] == 174

    def test_species_with_learnsets(self):
        lv = _load_json("learnset_validation.json")
        assert lv["species_with_learnsets"] >= 140

    def test_learnset_sizes(self):
        lv = _load_json("learnset_validation.json")
        sizes = lv["species_learnset_sizes"]
        assert len(sizes) >= 100
        for species, size in sizes.items():
            assert size >= 1, f"{species} has empty learnset"

    def test_starters_have_learnsets(self):
        lv = _load_json("learnset_validation.json")
        sizes = lv["species_learnset_sizes"]
        assert "Bulbasaur" in sizes
        assert "Charmander" in sizes
        assert "Squirtle" in sizes

    def test_invalid_moves_tracked(self):
        lv = _load_json("learnset_validation.json")
        assert "invalid_moves_found" in lv
        # Invalid moves exist due to moves not in moves.json
        assert isinstance(lv["invalid_moves_found"], list)


# ──── Trainer Dialogues ───────────────────────────────────────

class TestTrainerDialogues:
    def test_dialogue_count(self):
        td = _load_json("trainer_dialogues.json")
        assert len(td) == 29

    def test_all_have_fields(self):
        td = _load_json("trainer_dialogues.json")
        for dialogue in td:
            assert "trainer_id" in dialogue
            assert "pre_battle" in dialogue
            assert "post_battle" in dialogue

    def test_dialogues_not_empty(self):
        td = _load_json("trainer_dialogues.json")
        for dialogue in td:
            assert len(dialogue["pre_battle"]) > 0
            assert len(dialogue["post_battle"]) > 0

    def test_unique_trainer_ids(self):
        td = _load_json("trainer_dialogues.json")
        ids = [d["trainer_id"] for d in td]
        assert len(ids) == len(set(ids))

    def test_trainer_ids_match_route_teams(self):
        td = _load_json("trainer_dialogues.json")
        rt = _load_json("route_trainer_teams.json")
        route_ids = set()
        for entry in rt:
            for trainer in entry["trainers"]:
                route_ids.add(trainer["id"])
        dialogue_ids = {d["trainer_id"] for d in td}
        # All dialogue trainer IDs should exist in route teams
        for did in dialogue_ids:
            assert did in route_ids, \
                f"Dialogue trainer {did} not in route_trainer_teams.json"

    def test_pre_battle_has_personality(self):
        td = _load_json("trainer_dialogues.json")
        # Each dialogue should be unique
        pre_texts = [d["pre_battle"] for d in td]
        assert len(pre_texts) == len(set(pre_texts))

    def test_post_battle_different_from_pre(self):
        td = _load_json("trainer_dialogues.json")
        for dialogue in td:
            assert dialogue["pre_battle"] != dialogue["post_battle"]


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
