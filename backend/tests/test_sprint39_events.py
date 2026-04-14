"""Tests for Sprint 39: Gift Pokemon, in-game trades, trainer rematches.

These tests verify gift/event Pokemon, NPC trade offers,
and post-game trainer rematch data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Gift Pokemon ─────────────────────────────────────────────

class TestGiftPokemon:
    def test_gift_count(self):
        gifts = _load_json("gift_pokemon.json")
        assert len(gifts) == 11

    def test_all_gifts_have_fields(self):
        gifts = _load_json("gift_pokemon.json")
        for gift in gifts:
            assert "id" in gift
            assert "species" in gift
            assert "level" in gift
            assert "location" in gift
            assert "given_by" in gift
            assert "condition" in gift

    def test_three_starters(self):
        gifts = _load_json("gift_pokemon.json")
        starters = [g for g in gifts if "starter" in g["id"]]
        assert len(starters) == 3
        starter_species = {g["species"] for g in starters}
        assert starter_species == {"Bulbasaur", "Charmander", "Squirtle"}

    def test_starters_level_5(self):
        gifts = _load_json("gift_pokemon.json")
        for g in gifts:
            if "starter" in g["id"]:
                assert g["level"] == 5

    def test_eevee_gift(self):
        gifts = _load_json("gift_pokemon.json")
        eevee = next(g for g in gifts if g["species"] == "Eevee")
        assert eevee["location"] == "celadon_city"
        assert eevee["level"] == 25

    def test_lapras_gift(self):
        gifts = _load_json("gift_pokemon.json")
        lapras = next(g for g in gifts if g["species"] == "Lapras")
        assert lapras["location"] == "silph_co"

    def test_fossils(self):
        gifts = _load_json("gift_pokemon.json")
        fossils = [g for g in gifts if "fossil" in g["id"]]
        assert len(fossils) == 3
        fossil_species = {g["species"] for g in fossils}
        assert fossil_species == {"Omanyte", "Kabuto", "Aerodactyl"}

    def test_all_one_time(self):
        gifts = _load_json("gift_pokemon.json")
        for gift in gifts:
            assert gift["one_time"] is True

    def test_hitmon_choice(self):
        gifts = _load_json("gift_pokemon.json")
        hitmons = [g for g in gifts if "hitmon" in g["id"]]
        assert len(hitmons) == 2


# ──── In-Game Trades ───────────────────────────────────────────

class TestInGameTrades:
    def test_trade_count(self):
        trades = _load_json("ingame_trades.json")
        assert len(trades) == 8

    def test_all_trades_have_fields(self):
        trades = _load_json("ingame_trades.json")
        for trade in trades:
            assert "id" in trade
            assert "offered_species" in trade
            assert "requested_species" in trade
            assert "offered_nickname" in trade
            assert "location" in trade

    def test_farfetchd_trade(self):
        trades = _load_json("ingame_trades.json")
        dux = next(t for t in trades if t["offered_nickname"] == "DUX")
        assert dux["offered_species"] == "Farfetchd"
        assert dux["requested_species"] == "Spearow"

    def test_mr_mime_trade(self):
        trades = _load_json("ingame_trades.json")
        marcel = next(t for t in trades if t["offered_species"] == "Mr. Mime")
        assert marcel["requested_species"] == "Abra"

    def test_all_have_nicknames(self):
        trades = _load_json("ingame_trades.json")
        for trade in trades:
            assert len(trade["offered_nickname"]) > 0

    def test_cinnabar_trades(self):
        trades = _load_json("ingame_trades.json")
        cinnabar = [t for t in trades if t["location"] == "cinnabar_island"]
        assert len(cinnabar) == 3

    def test_unique_ids(self):
        trades = _load_json("ingame_trades.json")
        ids = [t["id"] for t in trades]
        assert len(ids) == len(set(ids))


# ──── Trainer Rematches ────────────────────────────────────────

class TestTrainerRematch:
    def test_rematch_count(self):
        rematches = _load_json("trainer_rematch.json")
        assert len(rematches) == 6

    def test_all_have_fields(self):
        rematches = _load_json("trainer_rematch.json")
        for rm in rematches:
            assert "trainer_id" in rm
            assert "original_location" in rm
            assert "rematch_condition" in rm
            assert "team" in rm

    def test_all_post_elite_four(self):
        rematches = _load_json("trainer_rematch.json")
        for rm in rematches:
            assert rm["rematch_condition"] == "post_elite_four"

    def test_rematch_levels_high(self):
        rematches = _load_json("trainer_rematch.json")
        for rm in rematches:
            for pokemon in rm["team"]:
                assert pokemon["level"] >= 40, (
                    f"Rematch {rm['trainer_id']} has low level: {pokemon['level']}"
                )

    def test_rematch_pokemon_have_moves(self):
        rematches = _load_json("trainer_rematch.json")
        for rm in rematches:
            for pokemon in rm["team"]:
                assert "species" in pokemon
                assert "level" in pokemon
                assert "moves" in pokemon
                assert len(pokemon["moves"]) >= 2

    def test_rematch_teams_evolved(self):
        rematches = _load_json("trainer_rematch.json")
        hiker = next(rm for rm in rematches if rm["trainer_id"] == "hiker_mt_moon")
        species = {p["species"] for p in hiker["team"]}
        assert "Golem" in species or "Rhydon" in species


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
