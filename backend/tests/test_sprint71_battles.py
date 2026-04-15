"""Tests for Sprint 71: Legendary encounters, rival battle progression, Elite Four config.

These tests verify legendary/static Pokemon encounters, rival battle
progression metadata, and Elite Four challenge configuration.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Legendary Encounters ───────────────────────────────────

class TestLegendaryEncounters:
    def test_encounter_count(self):
        le = _load_json("legendary_encounters.json")
        assert len(le["encounters"]) == 7

    def test_total_field_matches(self):
        le = _load_json("legendary_encounters.json")
        assert le["total_encounters"] == len(le["encounters"])

    def test_encounters_have_fields(self):
        le = _load_json("legendary_encounters.json")
        for enc in le["encounters"]:
            assert "id" in enc
            assert "pokemon" in enc
            assert "level" in enc
            assert "location" in enc
            assert "one_time" in enc
            assert "catch_rate" in enc

    def test_unique_encounter_ids(self):
        le = _load_json("legendary_encounters.json")
        ids = [e["id"] for e in le["encounters"]]
        assert len(ids) == len(set(ids))

    def test_bird_trio(self):
        le = _load_json("legendary_encounters.json")
        trio = le["bird_trio"]
        assert len(trio["members"]) == 3
        assert "Articuno" in trio["members"]
        assert "Zapdos" in trio["members"]
        assert "Moltres" in trio["members"]

    def test_bird_trio_level_50(self):
        le = _load_json("legendary_encounters.json")
        birds = [e for e in le["encounters"] if e["pokemon"] in le["bird_trio"]["members"]]
        for bird in birds:
            assert bird["level"] == 50

    def test_mewtwo_highest_level(self):
        le = _load_json("legendary_encounters.json")
        mewtwo = next(e for e in le["encounters"] if e["pokemon"] == "Mewtwo")
        assert mewtwo["level"] == 70
        assert mewtwo["prerequisite"] == "champion_defeated"

    def test_snorlax_encounters(self):
        le = _load_json("legendary_encounters.json")
        snorlax = [e for e in le["encounters"] if e["pokemon"] == "Snorlax"]
        assert len(snorlax) == 2
        for s in snorlax:
            assert s["prerequisite"] == "poke_flute"

    def test_all_one_time(self):
        le = _load_json("legendary_encounters.json")
        for enc in le["encounters"]:
            assert enc["one_time"] is True

    def test_legendary_rules(self):
        le = _load_json("legendary_encounters.json")
        rules = le["legendary_rules"]
        assert rules["master_ball_guaranteed"] is True
        assert rules["unique_battle_music"] is True


# ──── Rival Battle Progression ───────────────────────────────

class TestRivalBattleProgression:
    def test_encounter_count(self):
        rp = _load_json("rival_battle_progression.json")
        assert len(rp["encounters"]) == 8

    def test_total_field_matches(self):
        rp = _load_json("rival_battle_progression.json")
        assert rp["total_encounters"] == len(rp["encounters"])

    def test_encounters_have_fields(self):
        rp = _load_json("rival_battle_progression.json")
        for enc in rp["encounters"]:
            assert "id" in enc
            assert "battle_number" in enc
            assert "location" in enc
            assert "reward_money" in enc
            assert "team_size" in enc

    def test_battle_numbers_sequential(self):
        rp = _load_json("rival_battle_progression.json")
        numbers = [e["battle_number"] for e in rp["encounters"]]
        assert numbers == list(range(1, 9))

    def test_team_size_grows(self):
        rp = _load_json("rival_battle_progression.json")
        sizes = [e["team_size"] for e in rp["encounters"]]
        for i in range(1, len(sizes)):
            assert sizes[i] >= sizes[i - 1]

    def test_reward_money_increases(self):
        rp = _load_json("rival_battle_progression.json")
        rewards = [e["reward_money"] for e in rp["encounters"]]
        for i in range(1, len(rewards)):
            assert rewards[i] >= rewards[i - 1]

    def test_champion_battle_last(self):
        rp = _load_json("rival_battle_progression.json")
        last = rp["encounters"][-1]
        assert last["battle_number"] == 8
        assert last["location"] == "indigo_plateau"
        assert last["team_size"] == 6

    def test_starter_logic(self):
        rp = _load_json("rival_battle_progression.json")
        logic = rp["rival_starter_logic"]
        assert logic["player_chooses_bulbasaur"] == "Charmander"
        assert logic["player_chooses_charmander"] == "Squirtle"
        assert logic["player_chooses_squirtle"] == "Bulbasaur"

    def test_ids_match_rival_teams(self):
        rp = _load_json("rival_battle_progression.json")
        rt = _load_json("rival_teams.json")
        for enc in rp["encounters"]:
            assert enc["id"] in rt, f"{enc['id']} not in rival_teams.json"


# ──── Elite Four Config ──────────────────────────────────────

class TestEliteFourConfig:
    def test_four_members(self):
        e4 = _load_json("elite_four_config.json")
        assert len(e4["members"]) == 4

    def test_total_battles(self):
        e4 = _load_json("elite_four_config.json")
        assert e4["total_battles"] == 5

    def test_member_names(self):
        e4 = _load_json("elite_four_config.json")
        assert "Lorelei" in e4["members"]
        assert "Bruno" in e4["members"]
        assert "Agatha" in e4["members"]
        assert "Lance" in e4["members"]

    def test_champion_is_blue(self):
        e4 = _load_json("elite_four_config.json")
        assert e4["champion"] == "Blue"

    def test_entry_requirement(self):
        e4 = _load_json("elite_four_config.json")
        assert e4["entry_requirement"] == "8_badges"

    def test_challenge_rules(self):
        e4 = _load_json("elite_four_config.json")
        rules = e4["challenge_rules"]
        assert rules["must_fight_in_order"] is True
        assert rules["no_pokecenter_between_battles"] is True
        assert rules["blackout_restarts_from_first"] is True
        assert rules["party_not_healed_between_battles"] is True

    def test_first_clear_rewards(self):
        e4 = _load_json("elite_four_config.json")
        rewards = e4["reward"]["first_clear"]
        assert rewards["hall_of_fame_entry"] is True
        assert rewards["unlock_cerulean_cave"] is True
        assert rewards["credits_roll"] is True

    def test_rematch_available(self):
        e4 = _load_json("elite_four_config.json")
        rematch = e4["rematch"]
        assert rematch["available_after"] == "champion_defeated"
        assert rematch["unlimited_rematches"] is True
        assert rematch["level_increase"] == 10

    def test_members_in_elite_four_teams(self):
        e4 = _load_json("elite_four_config.json")
        e4t = _load_json("elite_four_teams.json")
        for member in e4["members"]:
            key = member.lower()
            assert key in e4t, f"{member} not in elite_four_teams.json"


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
