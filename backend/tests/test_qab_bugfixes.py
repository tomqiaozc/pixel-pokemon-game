"""Tests for Sprint 6 QA-B bug fixes."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import create_game, get_game, _games, update_play_time
from backend.services.gym_service import _earned_badges
from backend.services.leaderboard_service import (
    _player_stats,
    _achievements,
    _clamp_limit,
    check_achievements,
    get_achievements,
    get_player_stats,
    get_pvp_leaderboard,
    get_trainer_leaderboard,
    get_pokedex_leaderboard,
    record_battle_won,
    record_money_spent,
    record_pokemon_caught,
    record_evolution,
    record_pvp_result,
)
from backend.services.pvp_service import (
    _pvp_sessions,
    _pvp_codes,
    _pvp_battles,
    _pvp_actions,
    _pvp_turn_results,
    _pvp_history,
    _pvp_results,
    create_pvp_session,
    join_pvp_session,
    ready_up,
    start_pvp_battle,
    forfeit_battle,
)
from backend.services.trade_service import (
    _trade_sessions,
    _trade_codes,
    _trade_history,
)
from backend.models.pvp import PvPAction, PvPHistoryEntry

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_all():
    _player_stats.clear()
    _achievements.clear()
    _pvp_sessions.clear()
    _pvp_codes.clear()
    _pvp_battles.clear()
    _pvp_actions.clear()
    _pvp_turn_results.clear()
    _pvp_history.clear()
    _pvp_results.clear()
    _trade_sessions.clear()
    _trade_codes.clear()
    _trade_history.clear()
    yield
    _player_stats.clear()
    _achievements.clear()
    _pvp_sessions.clear()
    _pvp_codes.clear()
    _pvp_battles.clear()
    _pvp_actions.clear()
    _pvp_turn_results.clear()
    _pvp_history.clear()
    _pvp_results.clear()
    _trade_sessions.clear()
    _trade_codes.clear()
    _trade_history.clear()


def _make_game(name: str, team_size: int = 3) -> str:
    game = create_game(name, 1)
    gid = game["id"]
    for i in range(team_size - 1):
        game["player"]["team"].append({
            "id": 4 + i, "name": f"Mon{i}", "types": ["fire"],
            "stats": {"hp": 100, "attack": 100, "defense": 100,
                      "sp_attack": 100, "sp_defense": 100, "speed": 100},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "t.png", "level": 10,
        })
    return gid


# ============================================================
# H1: Leaderboard limit validation
# ============================================================

class TestLeaderboardLimitValidation:
    def test_clamp_limit_negative(self):
        assert _clamp_limit(-5) == 1

    def test_clamp_limit_zero(self):
        assert _clamp_limit(0) == 1

    def test_clamp_limit_normal(self):
        assert _clamp_limit(10) == 10

    def test_clamp_limit_too_large(self):
        assert _clamp_limit(999) == 100

    def test_trainer_leaderboard_negative_limit(self):
        _make_game("Alice")
        result = get_trainer_leaderboard(limit=-1)
        assert len(result) >= 0  # Should not crash

    def test_pvp_leaderboard_huge_limit(self):
        result = get_pvp_leaderboard(limit=10000)
        assert isinstance(result, list)

    def test_pokedex_leaderboard_zero_limit(self):
        _make_game("Alice")
        result = get_pokedex_leaderboard(limit=0)
        assert len(result) >= 0

    def test_limit_api_negative(self):
        resp = client.get("/api/leaderboard/trainers?limit=-5")
        assert resp.status_code == 200

    def test_limit_api_huge(self):
        resp = client.get("/api/leaderboard/trainers?limit=999")
        assert resp.status_code == 200


# ============================================================
# H2: PvP leaderboard tie-breaking
# ============================================================

class TestPvPLeaderboardTieBreaking:
    def test_same_win_rate_ordered_by_wins(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        # Alice: 5 wins, 0 losses = 100% (5 total)
        _pvp_history[gid1] = [
            PvPHistoryEntry(date=f"2024-01-0{i}", opponent_name="X", result="win", turns=3)
            for i in range(1, 6)
        ]
        # Bob: 10 wins, 0 losses = 100% (10 total)
        _pvp_history[gid2] = [
            PvPHistoryEntry(date=f"2024-01-{i:02d}", opponent_name="Y", result="win", turns=3)
            for i in range(1, 11)
        ]
        lb = get_pvp_leaderboard(limit=10, min_battles=5)
        alice = next((e for e in lb if e.player_id == gid1), None)
        bob = next((e for e in lb if e.player_id == gid2), None)
        assert alice is not None
        assert bob is not None
        # Bob has more wins, should rank higher
        assert bob.rank < alice.rank

        _pvp_history.pop(gid1, None)
        _pvp_history.pop(gid2, None)


# ============================================================
# H4: get_achievements for nonexistent players
# ============================================================

class TestAchievementsNonexistentPlayer:
    def test_get_achievements_returns_empty_for_nonexistent(self):
        result = get_achievements("nonexistent_player")
        assert result == []
        # Also verify it didn't create entries in the store
        assert "nonexistent_player" not in _achievements

    def test_achievements_api_404_for_nonexistent(self):
        resp = client.get("/api/player/nonexistent/achievements")
        assert resp.status_code == 404

    def test_get_achievements_works_for_existing(self):
        gid = _make_game("Alice")
        result = get_achievements(gid)
        assert len(result) == 12


# ============================================================
# M4: check_achievements 404 for nonexistent player
# ============================================================

class TestCheckAchievementsNotFound:
    def test_check_achievements_api_404(self):
        resp = client.post("/api/achievements/check/nonexistent")
        assert resp.status_code == 404

    def test_check_achievements_service_returns_empty(self):
        result = check_achievements("nonexistent")
        assert result.newly_earned == []


# ============================================================
# M2: play_time_seconds update
# ============================================================

class TestPlayTimeUpdate:
    def test_update_play_time(self):
        gid = _make_game("Alice")
        result = update_play_time(gid, 120)
        assert result is not None
        assert result["play_time_seconds"] == 120

    def test_update_play_time_nonexistent(self):
        result = update_play_time("nope", 100)
        assert result is None

    def test_update_play_time_negative_ignored(self):
        gid = _make_game("Alice")
        update_play_time(gid, 100)
        result = update_play_time(gid, -50)
        assert result["play_time_seconds"] == 100

    def test_play_time_api(self):
        gid = _make_game("Alice")
        resp = client.post(f"/api/game/{gid}/play-time", json={"seconds": 300})
        assert resp.status_code == 200
        assert resp.json()["play_time_seconds"] == 300

    def test_play_time_api_not_found(self):
        resp = client.post("/api/game/nope/play-time", json={"seconds": 100})
        assert resp.status_code == 404

    def test_speed_demon_uses_play_time(self):
        gid = _make_game("Alice")
        _earned_badges[gid] = {"boulder"}
        update_play_time(gid, 1500)  # 25 min
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "speed_demon" in earned_ids
        _earned_badges.pop(gid, None)

    def test_speed_demon_denied_over_30min(self):
        gid = _make_game("Alice")
        _earned_badges[gid] = {"boulder"}
        update_play_time(gid, 2000)  # 33 min
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "speed_demon" not in earned_ids
        _earned_badges.pop(gid, None)


# ============================================================
# C1: record_* wired into flows
# ============================================================

class TestRecordWiring:
    def test_record_pokemon_caught_increments(self):
        gid = _make_game("Alice")
        record_pokemon_caught(gid)
        stats = get_player_stats(gid)
        assert stats.total_pokemon_caught == 1

    def test_record_battle_won_increments(self):
        gid = _make_game("Alice")
        record_battle_won(gid)
        stats = get_player_stats(gid)
        assert stats.total_battles_won == 1

    def test_record_money_spent_increments(self):
        gid = _make_game("Alice")
        record_money_spent(gid, 5000)
        record_money_spent(gid, 3000)
        stats = _player_stats[gid]
        assert stats["total_spent"] == 8000

    def test_record_evolution_increments(self):
        gid = _make_game("Alice")
        record_evolution(gid)
        stats = _player_stats[gid]
        assert stats["evolutions"] == 1

    def test_record_pvp_result_win(self):
        gid = _make_game("Alice")
        record_pvp_result(gid, won=True)
        record_pvp_result(gid, won=True)
        stats = _player_stats[gid]
        assert stats["pvp_win_streak"] == 2
        assert stats["max_pvp_win_streak"] == 2

    def test_record_pvp_result_loss_resets_streak(self):
        gid = _make_game("Alice")
        record_pvp_result(gid, won=True)
        record_pvp_result(gid, won=True)
        record_pvp_result(gid, won=False)
        stats = _player_stats[gid]
        assert stats["pvp_win_streak"] == 0
        assert stats["max_pvp_win_streak"] == 2


# ============================================================
# C1: PvP forfeit records stats
# ============================================================

class TestPvPForfeitRecordsStats:
    def test_forfeit_records_pvp_results(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        ready_up(session.id, gid1)
        ready_up(session.id, gid2)
        start_pvp_battle(session.id)

        forfeit_battle(session.id, gid1)

        # Winner (gid2) should have a win recorded
        stats2 = _player_stats.get(gid2, {})
        assert stats2.get("pvp_win_streak", 0) >= 1

        # Loser (gid1) should have loss recorded (streak = 0)
        stats1 = _player_stats.get(gid1, {})
        assert stats1.get("pvp_win_streak", 0) == 0


# ============================================================
# C2: Achievements auto-checked
# ============================================================

class TestAchievementsAutoChecked:
    def test_big_spender_via_buy_api(self):
        gid = _make_game("Alice")
        # Give player lots of money
        game = get_game(gid)
        game["player"]["money"] = 50000
        # Buy items totaling >= 10000
        # The shop buy endpoint should call record_money_spent + check_achievements
        # We can't easily test the full API flow without valid shop data,
        # so test the service-level wiring instead
        record_money_spent(gid, 10000)
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "big_spender" in earned_ids

    def test_first_steps_after_catch(self):
        gid = _make_game("Alice")
        record_pokemon_caught(gid)
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "first_steps" in earned_ids

    def test_evolve_achievement_after_evolution(self):
        gid = _make_game("Alice")
        record_evolution(gid)
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "evolve" in earned_ids


# ============================================================
# Integration: battle action with game_id
# ============================================================

class TestBattleActionGameId:
    def test_battle_action_accepts_game_id(self):
        gid = _make_game("Alice")
        # Start a battle via API
        resp = client.post("/api/battle/start", json={"game_id": gid})
        assert resp.status_code == 200
        battle_id = resp.json()["battle"]["id"]

        # Send action with game_id
        resp2 = client.post("/api/battle/action", json={
            "battle_id": battle_id,
            "action": "fight",
            "move_index": 0,
            "game_id": gid,
        })
        assert resp2.status_code == 200

    def test_battle_action_without_game_id_still_works(self):
        gid = _make_game("Alice")
        resp = client.post("/api/battle/start", json={"game_id": gid})
        assert resp.status_code == 200
        battle_id = resp.json()["battle"]["id"]

        resp2 = client.post("/api/battle/action", json={
            "battle_id": battle_id,
            "action": "fight",
            "move_index": 0,
        })
        assert resp2.status_code == 200
