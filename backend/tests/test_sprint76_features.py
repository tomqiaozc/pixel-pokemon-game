"""Tests for Sprint 76: Battle UI config, link cable trading, slot machine.

These tests verify battle UI layout, trading system rules,
and slot machine minigame configuration.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Battle UI Config ───────────────────────────────────────

class TestBattleUIConfig:
    def test_screen_dimensions(self):
        ui = _load_json("battle_ui_config.json")
        assert ui["layout"]["screen_width"] == 240
        assert ui["layout"]["screen_height"] == 160

    def test_hp_bar_colors(self):
        ui = _load_json("battle_ui_config.json")
        hp = ui["hp_bar"]
        assert "high" in hp["colors"]
        assert "medium" in hp["colors"]
        assert "low" in hp["colors"]

    def test_hp_bar_thresholds(self):
        ui = _load_json("battle_ui_config.json")
        th = ui["hp_bar"]["thresholds"]
        assert th["high_above"] == 0.5
        assert th["low_at_or_below"] == 0.2

    def test_action_menu_options(self):
        ui = _load_json("battle_ui_config.json")
        options = ui["action_menu"]["options"]
        assert len(options) == 4
        assert "FIGHT" in options
        assert "RUN" in options

    def test_move_menu_shows_pp(self):
        ui = _load_json("battle_ui_config.json")
        assert ui["move_menu"]["shows_pp"] is True
        assert ui["move_menu"]["shows_type"] is True

    def test_status_icons(self):
        ui = _load_json("battle_ui_config.json")
        icons = ui["status_icons"]
        assert len(icons) == 5
        assert ui["total_status_icons"] == 5
        assert "poison" in icons
        assert "burn" in icons

    def test_text_speed_options(self):
        ui = _load_json("battle_ui_config.json")
        speeds = ui["text_speed_options"]
        assert speeds["slow"] > speeds["medium"] > speeds["fast"]

    def test_exp_bar_player_only(self):
        ui = _load_json("battle_ui_config.json")
        assert ui["exp_bar"]["shows_for_player_only"] is True


# ──── Link Cable Trading ─────────────────────────────────────

class TestLinkCableTrading:
    def test_available_centers(self):
        lt = _load_json("link_cable_trading.json")
        assert len(lt["available_centers"]) == 4

    def test_trade_evolution_count(self):
        lt = _load_json("link_cable_trading.json")
        assert len(lt["trade_evolution_pokemon"]) == 4
        assert lt["total_trade_evolutions"] == 4

    def test_trade_evolutions_correct(self):
        lt = _load_json("link_cable_trading.json")
        evos = {te["pokemon"]: te["evolves_to"] for te in lt["trade_evolution_pokemon"]}
        assert evos["Kadabra"] == "Alakazam"
        assert evos["Haunter"] == "Gengar"

    def test_trade_steps(self):
        lt = _load_json("link_cable_trading.json")
        assert len(lt["trade_flow"]) == 6
        assert lt["total_trade_steps"] == 6

    def test_cannot_trade_last(self):
        lt = _load_json("link_cable_trading.json")
        assert lt["trade_rules"]["cannot_trade_last_pokemon"] is True

    def test_traded_exp_bonus(self):
        lt = _load_json("link_cable_trading.json")
        tp = lt["traded_pokemon_properties"]
        assert tp["gains_boosted_exp"] is True
        assert tp["exp_multiplier"] == 1.5

    def test_nickname_locked(self):
        lt = _load_json("link_cable_trading.json")
        assert lt["traded_pokemon_properties"]["nickname_cannot_be_changed"] is True

    def test_dialogue_entries(self):
        lt = _load_json("link_cable_trading.json")
        assert len(lt["dialogue"]) >= 5


# ──── Slot Machine Game ──────────────────────────────────────

class TestSlotMachineGame:
    def test_machine_count(self):
        sm = _load_json("slot_machine_game.json")
        assert sm["machine_count"] == 30

    def test_cost_per_play(self):
        sm = _load_json("slot_machine_game.json")
        assert sm["cost_per_play"] == 3

    def test_reel_symbols(self):
        sm = _load_json("slot_machine_game.json")
        symbols = sm["reels"]["symbols"]
        assert len(symbols) == 6
        assert sm["total_symbols"] == 6

    def test_three_reels(self):
        sm = _load_json("slot_machine_game.json")
        assert sm["reels"]["count"] == 3

    def test_payouts(self):
        sm = _load_json("slot_machine_game.json")
        payouts = sm["payouts"]
        assert len(payouts) == 6
        assert sm["total_payouts"] == 6

    def test_jackpot_highest(self):
        sm = _load_json("slot_machine_game.json")
        jackpot = next(p for p in sm["payouts"] if p["name"] == "Jackpot")
        assert jackpot["payout"] == 300

    def test_lucky_machines(self):
        sm = _load_json("slot_machine_game.json")
        lucky = sm["lucky_machines"]
        assert lucky["exist"] is True
        assert lucky["count"] == 3
        assert lucky["payout_multiplier"] == 1.5

    def test_max_coins(self):
        sm = _load_json("slot_machine_game.json")
        assert sm["max_coins"] == 9999

    def test_coin_case_required(self):
        sm = _load_json("slot_machine_game.json")
        assert sm["coin_case_required"] is True

    def test_location(self):
        sm = _load_json("slot_machine_game.json")
        assert sm["location"] == "celadon_game_corner"


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
