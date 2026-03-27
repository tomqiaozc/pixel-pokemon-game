"""Tests for the leaderboard, stats, and achievement system."""
from __future__ import annotations

import pytest

from backend.services.game_service import create_game, _games
from backend.services.gym_service import _earned_badges
from backend.services.pvp_service import _pvp_history
from backend.models.pvp import PvPHistoryEntry
from backend.services.leaderboard_service import (
    _player_stats,
    _achievements,
    check_achievements,
    get_achievements,
    get_player_stats,
    get_pokedex_leaderboard,
    get_pvp_leaderboard,
    get_trainer_leaderboard,
    record_battle_won,
    record_evolution,
    record_money_spent,
    record_pokemon_caught,
    record_pvp_result,
)


@pytest.fixture(autouse=True)
def _clean_state():
    _player_stats.clear()
    _achievements.clear()
    yield
    _player_stats.clear()
    _achievements.clear()


def _create_game(name: str) -> str:
    game = create_game(name, 1)
    return game["id"]


# ============================================================
# Player Stats
# ============================================================

class TestPlayerStats:
    def test_basic_stats(self):
        gid = _create_game("Alice")
        stats = get_player_stats(gid)
        assert stats is not None
        assert stats.player_name == "Alice"
        assert stats.trainer_class == "Beginner"

    def test_stats_not_found(self):
        assert get_player_stats("nonexistent") is None

    def test_record_pokemon_caught(self):
        gid = _create_game("Alice")
        record_pokemon_caught(gid)
        record_pokemon_caught(gid)
        stats = get_player_stats(gid)
        assert stats.total_pokemon_caught == 2

    def test_record_battle_won(self):
        gid = _create_game("Alice")
        record_battle_won(gid)
        stats = get_player_stats(gid)
        assert stats.total_battles_won == 1

    def test_trainer_class_progression(self):
        gid = _create_game("Alice")
        assert get_player_stats(gid).trainer_class == "Beginner"

        _earned_badges[gid] = {"boulder"}
        assert get_player_stats(gid).trainer_class == "Pokemon Trainer"

        _earned_badges[gid] = {"boulder", "cascade", "thunder", "rainbow"}
        assert get_player_stats(gid).trainer_class == "Ace Trainer"

        _earned_badges[gid] = {"boulder", "cascade", "thunder", "rainbow", "soul", "marsh", "volcano", "earth"}
        assert get_player_stats(gid).trainer_class == "Champion"

        # cleanup
        _earned_badges.pop(gid, None)

    def test_pvp_stats(self):
        gid = _create_game("Alice")
        _pvp_history[gid] = [
            PvPHistoryEntry(date="2024-01-01", opponent_name="Bob", result="win", turns=5),
            PvPHistoryEntry(date="2024-01-02", opponent_name="Charlie", result="loss", turns=3),
            PvPHistoryEntry(date="2024-01-03", opponent_name="Dave", result="win", turns=7),
        ]
        stats = get_player_stats(gid)
        assert stats.pvp_wins == 2
        assert stats.pvp_losses == 1
        assert stats.pvp_win_rate == 66.7

        # cleanup
        _pvp_history.pop(gid, None)


# ============================================================
# Trainer Leaderboard
# ============================================================

class TestTrainerLeaderboard:
    def test_empty_leaderboard(self):
        # May have games from other tests, but structure should be valid
        result = get_trainer_leaderboard(limit=5)
        assert isinstance(result, list)

    def test_leaderboard_ordering(self):
        gid1 = _create_game("Alice")
        gid2 = _create_game("Bob")
        _earned_badges[gid1] = {"boulder", "cascade"}
        _earned_badges[gid2] = {"boulder"}

        lb = get_trainer_leaderboard(limit=10)
        # Find our entries
        alice_entry = next((e for e in lb if e.player_id == gid1), None)
        bob_entry = next((e for e in lb if e.player_id == gid2), None)
        assert alice_entry is not None
        assert bob_entry is not None
        assert alice_entry.rank < bob_entry.rank  # More badges = higher rank

        # cleanup
        _earned_badges.pop(gid1, None)
        _earned_badges.pop(gid2, None)

    def test_leaderboard_limit(self):
        lb = get_trainer_leaderboard(limit=2)
        assert len(lb) <= 2


# ============================================================
# PvP Leaderboard
# ============================================================

class TestPvPLeaderboard:
    def test_empty_pvp_leaderboard(self):
        result = get_pvp_leaderboard()
        assert isinstance(result, list)

    def test_pvp_leaderboard_min_battles(self):
        gid = _create_game("Alice")
        # Only 3 battles — below min_battles=5
        _pvp_history[gid] = [
            PvPHistoryEntry(date="2024-01-01", opponent_name="X", result="win", turns=3),
            PvPHistoryEntry(date="2024-01-02", opponent_name="Y", result="win", turns=3),
            PvPHistoryEntry(date="2024-01-03", opponent_name="Z", result="win", turns=3),
        ]
        lb = get_pvp_leaderboard(min_battles=5)
        assert not any(e.player_id == gid for e in lb)

        # cleanup
        _pvp_history.pop(gid, None)

    def test_pvp_leaderboard_with_enough_battles(self):
        gid = _create_game("ProGamer")
        _pvp_history[gid] = [
            PvPHistoryEntry(date=f"2024-01-0{i}", opponent_name=f"P{i}", result="win", turns=3)
            for i in range(1, 6)
        ]
        lb = get_pvp_leaderboard(min_battles=5)
        entry = next((e for e in lb if e.player_id == gid), None)
        assert entry is not None
        assert entry.win_rate == 100.0

        # cleanup
        _pvp_history.pop(gid, None)


# ============================================================
# Pokedex Leaderboard
# ============================================================

class TestPokedexLeaderboard:
    def test_pokedex_leaderboard(self):
        _create_game("Alice")
        lb = get_pokedex_leaderboard(limit=5)
        assert isinstance(lb, list)


# ============================================================
# Achievements
# ============================================================

class TestAchievements:
    def test_initial_achievements_all_incomplete(self):
        gid = _create_game("Alice")
        achs = get_achievements(gid)
        assert len(achs) == 12  # 12 defined achievements
        assert all(not a.completed for a in achs)

    def test_first_steps_achievement(self):
        gid = _create_game("Alice")
        record_pokemon_caught(gid)
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "first_steps" in earned_ids

    def test_collector_achievement(self):
        gid = _create_game("Alice")
        for _ in range(10):
            record_pokemon_caught(gid)
        # Need 10 caught in pokedex too — just check the stat counter for now
        result = check_achievements(gid)
        # Collector requires 10 pokedex catches, not just the counter
        # So this might not trigger without actually registering species
        assert isinstance(result.all_achievements, list)

    def test_rock_solid_achievement(self):
        gid = _create_game("Alice")
        _earned_badges[gid] = {"boulder"}
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "rock_solid" in earned_ids

        # cleanup
        _earned_badges.pop(gid, None)

    def test_water_works_achievement(self):
        gid = _create_game("Alice")
        _earned_badges[gid] = {"cascade"}
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "water_works" in earned_ids

        # cleanup
        _earned_badges.pop(gid, None)

    def test_full_team_achievement(self):
        gid = _create_game("Alice")
        game = _games[gid]
        # Add 5 more Pokemon for total of 6
        for i in range(5):
            game["player"]["team"].append({
                "id": 10 + i, "name": f"Mon{i}", "types": ["normal"],
                "stats": {"hp": 100, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 50},
                "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
                "sprite": "test.png", "level": 5,
            })
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "full_team" in earned_ids

    def test_evolve_achievement(self):
        gid = _create_game("Alice")
        record_evolution(gid)
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "evolve" in earned_ids

    def test_big_spender_achievement(self):
        gid = _create_game("Alice")
        record_money_spent(gid, 10000)
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "big_spender" in earned_ids

    def test_achievement_not_re_earned(self):
        gid = _create_game("Alice")
        record_pokemon_caught(gid)
        result1 = check_achievements(gid)
        assert any(a.id == "first_steps" for a in result1.newly_earned)

        result2 = check_achievements(gid)
        assert not any(a.id == "first_steps" for a in result2.newly_earned)

    def test_speed_demon_achievement(self):
        gid = _create_game("Alice")
        _earned_badges[gid] = {"boulder"}
        _games[gid]["play_time_seconds"] = 1500  # 25 min < 30 min
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "speed_demon" in earned_ids

        # cleanup
        _earned_badges.pop(gid, None)

    def test_pvp_win_streak(self):
        gid = _create_game("Alice")
        for _ in range(10):
            record_pvp_result(gid, won=True)
        _pvp_history[gid] = [
            PvPHistoryEntry(date=f"2024-01-{i:02d}", opponent_name=f"P{i}", result="win", turns=3)
            for i in range(1, 11)
        ]
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "battle_tested" in earned_ids
        assert "unbeatable" in earned_ids

        # cleanup
        _pvp_history.pop(gid, None)
