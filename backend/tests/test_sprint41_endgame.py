"""Tests for Sprint 41: Elite Four teams, Hall of Fame, post-game content.

These tests verify detailed Elite Four team data, Hall of Fame recording,
and post-champion unlock content.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Elite Four Teams ─────────────────────────────────────────

class TestEliteFourTeams:
    def test_four_members(self):
        e4 = _load_json("elite_four_teams.json")
        assert len(e4) == 4

    MEMBERS = ["lorelei", "bruno", "agatha", "lance"]

    @pytest.mark.parametrize("member_id", MEMBERS)
    def test_member_exists(self, member_id):
        e4 = _load_json("elite_four_teams.json")
        assert member_id in e4
        member = e4[member_id]
        assert "name" in member
        assert "specialty" in member
        assert "team" in member
        assert "pre_battle_dialogue" in member
        assert "defeat_dialogue" in member

    def test_all_have_5_pokemon(self):
        e4 = _load_json("elite_four_teams.json")
        for mid, member in e4.items():
            assert len(member["team"]) == 5, f"{mid} has {len(member['team'])} Pokemon"

    def test_lance_highest_level(self):
        e4 = _load_json("elite_four_teams.json")
        lance_max = max(p["level"] for p in e4["lance"]["team"])
        for mid, member in e4.items():
            if mid != "lance":
                member_max = max(p["level"] for p in member["team"])
                assert member_max <= lance_max

    def test_dragonite_lance_ace(self):
        e4 = _load_json("elite_four_teams.json")
        dragonite = next(p for p in e4["lance"]["team"] if p["species"] == "Dragonite")
        assert dragonite["level"] == 62

    def test_all_pokemon_have_moves(self):
        e4 = _load_json("elite_four_teams.json")
        for mid, member in e4.items():
            for pokemon in member["team"]:
                assert "moves" in pokemon
                assert len(pokemon["moves"]) >= 3

    def test_held_items_present(self):
        e4 = _load_json("elite_four_teams.json")
        held_items = []
        for mid, member in e4.items():
            for pokemon in member["team"]:
                if pokemon.get("held_item"):
                    held_items.append(pokemon["held_item"])
        assert len(held_items) >= 3

    def test_abilities_present(self):
        e4 = _load_json("elite_four_teams.json")
        for mid, member in e4.items():
            for pokemon in member["team"]:
                assert "ability" in pokemon

    SPECIALTIES = [("lorelei", "ice"), ("bruno", "fighting"), ("agatha", "ghost"), ("lance", "dragon")]

    @pytest.mark.parametrize("member_id,specialty", SPECIALTIES)
    def test_specialties(self, member_id, specialty):
        e4 = _load_json("elite_four_teams.json")
        assert e4[member_id]["specialty"] == specialty


# ──── Hall of Fame ─────────────────────────────────────────────

class TestHallOfFame:
    def test_file_exists(self):
        hof = _load_json("hall_of_fame.json")
        assert "description" in hof

    def test_max_entries(self):
        hof = _load_json("hall_of_fame.json")
        assert hof["max_entries"] == 50

    def test_record_format(self):
        hof = _load_json("hall_of_fame.json")
        fmt = hof["record_format"]
        assert "entry_number" in fmt
        assert "player_name" in fmt
        assert "team" in fmt

    def test_first_completion_rewards(self):
        hof = _load_json("hall_of_fame.json")
        rewards = hof["rewards"]["first_completion"]
        assert rewards["unlock_cerulean_cave"] is True
        assert rewards["national_dex_upgrade"] is True
        assert rewards["trainer_rematches_available"] is True


# ──── Post-Game Content ────────────────────────────────────────

class TestPostGameContent:
    def test_file_exists(self):
        pg = _load_json("postgame_content.json")
        assert "unlocked_after_champion" in pg

    def test_unlock_count(self):
        pg = _load_json("postgame_content.json")
        assert len(pg["unlocked_after_champion"]) >= 5

    def test_cerulean_cave_unlock(self):
        pg = _load_json("postgame_content.json")
        unlocks = pg["unlocked_after_champion"]
        cave = next(u for u in unlocks if u["id"] == "cerulean_cave")
        assert cave["type"] == "dungeon"

    def test_trainer_rematches_unlock(self):
        pg = _load_json("postgame_content.json")
        unlocks = pg["unlocked_after_champion"]
        rematches = next(u for u in unlocks if u["id"] == "trainer_rematches")
        assert rematches["type"] == "feature"

    def test_daily_events(self):
        pg = _load_json("postgame_content.json")
        assert len(pg["daily_events"]) >= 3

    def test_completion_rewards(self):
        pg = _load_json("postgame_content.json")
        rewards = pg["completion_rewards"]
        assert "pokedex_50" in rewards
        assert "pokedex_100" in rewards
        assert "pokedex_151" in rewards

    def test_diploma_for_completion(self):
        pg = _load_json("postgame_content.json")
        assert pg["completion_rewards"]["pokedex_151"]["reward"] == "Diploma"


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
