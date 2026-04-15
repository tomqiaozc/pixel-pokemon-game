"""Tests for Sprint 73: EXP gain formula, trainer prize money, Pokedex evaluation.

These tests verify experience gain configuration, trainer class payouts,
and Pokedex evaluation thresholds and rewards.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── EXP Gain Formula ───────────────────────────────────────

class TestExpGainFormula:
    def test_has_base_formula(self):
        eg = _load_json("exp_gain_formula.json")
        assert "base_formula" in eg
        assert "description" in eg["base_formula"]

    def test_traded_bonus(self):
        eg = _load_json("exp_gain_formula.json")
        assert eg["modifiers"]["traded_pokemon"]["multiplier"] == 1.5

    def test_trainer_bonus(self):
        eg = _load_json("exp_gain_formula.json")
        assert eg["modifiers"]["trainer_pokemon"]["multiplier"] == 1.5

    def test_lucky_egg_bonus(self):
        eg = _load_json("exp_gain_formula.json")
        assert eg["modifiers"]["lucky_egg"]["multiplier"] == 1.5

    def test_exp_share_config(self):
        eg = _load_json("exp_gain_formula.json")
        es = eg["exp_share_config"]
        assert es["item_name"] == "Exp. Share"
        assert es["obtain_location"] == "route_15"
        assert es["splits_exp"] is True

    def test_lucky_egg_from_chansey(self):
        eg = _load_json("exp_gain_formula.json")
        le = eg["lucky_egg_config"]
        assert le["obtain_method"] == "wild_chansey"
        assert le["hold_chance_percent"] == 5

    def test_level_cap(self):
        eg = _load_json("exp_gain_formula.json")
        assert eg["level_cap"] == 100

    def test_exp_on_faint(self):
        eg = _load_json("exp_gain_formula.json")
        assert eg["exp_on_faint_only"] is True


# ──── Trainer Prize Money ────────────────────────────────────

class TestTrainerPrizeMoney:
    def test_class_payout_count(self):
        tp = _load_json("trainer_prize_money.json")
        assert len(tp["class_payouts"]) == 24

    def test_total_classes_match(self):
        tp = _load_json("trainer_prize_money.json")
        assert tp["total_trainer_classes"] == len(tp["class_payouts"])

    def test_payouts_have_fields(self):
        tp = _load_json("trainer_prize_money.json")
        for cp in tp["class_payouts"]:
            assert "class" in cp
            assert "base_payout" in cp
            assert cp["base_payout"] > 0

    def test_badge_multipliers(self):
        tp = _load_json("trainer_prize_money.json")
        bm = tp["badge_multipliers"]
        assert len(bm) == 9
        assert bm["0"] == 1.0
        assert bm["8"] == 2.5

    def test_gym_leader_payout(self):
        tp = _load_json("trainer_prize_money.json")
        gl = next(c for c in tp["class_payouts"] if c["class"] == "Gym Leader")
        assert gl["base_payout"] == 100

    def test_champion_highest_payout(self):
        tp = _load_json("trainer_prize_money.json")
        champ = next(c for c in tp["class_payouts"] if c["class"] == "Champion")
        assert champ["base_payout"] == 120

    def test_amulet_coin(self):
        tp = _load_json("trainer_prize_money.json")
        ac = tp["amulet_coin"]
        assert ac["multiplier"] == 2.0

    def test_loss_penalty(self):
        tp = _load_json("trainer_prize_money.json")
        lp = tp["loss_penalty"]
        assert lp["player_loses_half_money"] is True
        assert lp["minimum_money_after_loss"] == 0

    def test_pay_day_move(self):
        tp = _load_json("trainer_prize_money.json")
        pd = tp["pay_day_move"]
        assert pd["move_name"] == "Pay Day"


# ──── Pokedex Evaluation ─────────────────────────────────────

class TestPokedexEvaluation:
    def test_evaluation_count(self):
        pe = _load_json("pokedex_evaluation.json")
        assert len(pe["evaluation_thresholds"]) == 10

    def test_total_evaluations_match(self):
        pe = _load_json("pokedex_evaluation.json")
        assert pe["total_evaluations"] == len(pe["evaluation_thresholds"])

    def test_evaluations_have_fields(self):
        pe = _load_json("pokedex_evaluation.json")
        for ev in pe["evaluation_thresholds"]:
            assert "caught" in ev
            assert "rating" in ev

    def test_starts_at_zero(self):
        pe = _load_json("pokedex_evaluation.json")
        assert pe["evaluation_thresholds"][0]["caught"] == 0

    def test_ends_at_151(self):
        pe = _load_json("pokedex_evaluation.json")
        assert pe["evaluation_thresholds"][-1]["caught"] == 151

    def test_thresholds_ascending(self):
        pe = _load_json("pokedex_evaluation.json")
        counts = [e["caught"] for e in pe["evaluation_thresholds"]]
        for i in range(1, len(counts)):
            assert counts[i] > counts[i - 1]

    def test_completion_rewards(self):
        pe = _load_json("pokedex_evaluation.json")
        rewards = pe["completion_rewards"]
        assert "seen_all_151" in rewards
        assert "caught_all_151" in rewards

    def test_oaks_aide_rewards(self):
        pe = _load_json("pokedex_evaluation.json")
        aides = pe["oaks_aide_rewards"]
        assert len(aides) == 5
        assert pe["total_aide_rewards"] == 5

    def test_aide_rewards_have_fields(self):
        pe = _load_json("pokedex_evaluation.json")
        for aide in pe["oaks_aide_rewards"]:
            assert "pokemon_caught" in aide
            assert "location" in aide
            assert "reward" in aide

    def test_total_pokemon(self):
        pe = _load_json("pokedex_evaluation.json")
        assert pe["total_pokemon"] == 151


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
