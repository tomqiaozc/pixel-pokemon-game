"""Additional edge-case and integration tests for Sprint 6 features."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.trade import TradeResult, TradeSession
from backend.models.pvp import PvPAction, PvPBattleResult, PvPTurnResult
from backend.services.game_service import create_game, _games
from backend.services.trade_service import (
    _trade_sessions,
    _trade_codes,
    _trade_history,
    SESSION_TIMEOUT_SECONDS as TRADE_TIMEOUT,
    cancel_offer,
    confirm_trade,
    create_trade_session,
    get_trade_session,
    join_trade_session,
    set_trade_offer,
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
    forfeit_battle,
    get_pvp_session,
    join_pvp_session,
    ready_up,
    start_pvp_battle,
    submit_action,
)
from backend.services.leaderboard_service import (
    _player_stats,
    _achievements,
    check_achievements,
    get_player_stats,
    record_pokemon_caught,
    record_pvp_result,
)
from backend.services.gym_service import _earned_badges

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_all():
    _trade_sessions.clear()
    _trade_codes.clear()
    _trade_history.clear()
    _pvp_sessions.clear()
    _pvp_codes.clear()
    _pvp_battles.clear()
    _pvp_actions.clear()
    _pvp_turn_results.clear()
    _pvp_history.clear()
    _pvp_results.clear()
    _player_stats.clear()
    _achievements.clear()
    yield
    _trade_sessions.clear()
    _trade_codes.clear()
    _trade_history.clear()
    _pvp_sessions.clear()
    _pvp_codes.clear()
    _pvp_battles.clear()
    _pvp_actions.clear()
    _pvp_turn_results.clear()
    _pvp_history.clear()
    _pvp_results.clear()
    _player_stats.clear()
    _achievements.clear()


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
# Trade: Session Expiry
# ============================================================

class TestTradeExpiry:
    def test_expired_session_returns_none(self):
        gid = _make_game("Alice")
        session = create_trade_session(gid)
        # Backdate last_activity
        session.last_activity = datetime.now(timezone.utc) - timedelta(seconds=TRADE_TIMEOUT + 10)
        assert get_trade_session(session.id) is None

    def test_join_expired_session_raises(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_trade_session(gid1)
        session.last_activity = datetime.now(timezone.utc) - timedelta(seconds=TRADE_TIMEOUT + 10)
        with pytest.raises(ValueError, match="expired"):
            join_trade_session(session.trade_code, gid2)

    def test_offer_on_expired_session_raises(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        session.last_activity = datetime.now(timezone.utc) - timedelta(seconds=TRADE_TIMEOUT + 10)
        with pytest.raises(ValueError, match="expired"):
            set_trade_offer(session.id, gid1, 0)


# ============================================================
# Trade: Player2 Offer & Confirm
# ============================================================

class TestTradePlayer2Flow:
    def test_player2_can_offer(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        updated = set_trade_offer(session.id, gid2, 1)
        assert updated.player2_offer is not None
        assert updated.player2_offer.pokemon_index == 1

    def test_player2_confirm_without_offer_fails(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        with pytest.raises(ValueError, match="No offer set"):
            confirm_trade(session.id, gid2)

    def test_cancel_offer_by_player2(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid2, 0)
        updated = cancel_offer(session.id, gid2)
        assert updated.player2_offer is None

    def test_cancel_by_non_participant_fails(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        gid3 = _make_game("Charlie")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="not in this trade"):
            cancel_offer(session.id, gid3)


# ============================================================
# Trade: Negative Index
# ============================================================

class TestTradeNegativeIndex:
    def test_negative_pokemon_index_rejected(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="Invalid Pokemon index"):
            set_trade_offer(session.id, gid1, -1)


# ============================================================
# Trade: Multiple Consecutive Trades Build History
# ============================================================

class TestMultipleTrades:
    def test_multiple_trades_accumulate_history(self):
        gid1 = _make_game("Alice", team_size=5)
        gid2 = _make_game("Bob", team_size=5)

        for i in range(2):
            session = create_trade_session(gid1)
            join_trade_session(session.trade_code, gid2)
            set_trade_offer(session.id, gid1, 0)
            set_trade_offer(session.id, gid2, 0)
            confirm_trade(session.id, gid1)
            confirm_trade(session.id, gid2)

        from backend.services.trade_service import get_trade_history
        assert len(get_trade_history(gid1)) == 2
        assert len(get_trade_history(gid2)) == 2


# ============================================================
# Trade: Team Size After Trade
# ============================================================

class TestTradeTeamIntegrity:
    def test_team_sizes_preserved_after_trade(self):
        gid1 = _make_game("Alice", team_size=3)
        gid2 = _make_game("Bob", team_size=4)

        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        confirm_trade(session.id, gid2)

        from backend.services.trade_service import get_player_team
        assert len(get_player_team(gid1)) == 3
        assert len(get_player_team(gid2)) == 4


# ============================================================
# PvP: Edge Cases
# ============================================================

class TestPvPEdgeCases:
    def test_submit_action_after_battle_over_fails(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        ready_up(session.id, gid1)
        ready_up(session.id, gid2)
        start_pvp_battle(session.id)

        # Forfeit to end battle
        forfeit_battle(session.id, gid1)

        action = PvPAction(action="fight", move_index=0)
        with pytest.raises(ValueError, match="Battle has not started"):
            submit_action(session.id, gid1, action)

    def test_start_already_battling_returns_existing(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        ready_up(session.id, gid1)
        ready_up(session.id, gid2)
        b1 = start_pvp_battle(session.id)
        b2 = start_pvp_battle(session.id)
        assert b1.id == b2.id

    def test_pvp_session_expiry(self):
        from backend.services.pvp_service import SESSION_TIMEOUT_SECONDS as PVP_TIMEOUT
        gid = _make_game("Alice")
        session = create_pvp_session(gid)
        session.last_activity = datetime.now(timezone.utc) - timedelta(seconds=PVP_TIMEOUT + 10)
        assert get_pvp_session(session.id) is None

    def test_forfeit_player2_wins(self):
        gid1 = _make_game("Alice")
        gid2 = _make_game("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        ready_up(session.id, gid1)
        ready_up(session.id, gid2)
        start_pvp_battle(session.id)
        result = forfeit_battle(session.id, gid2)
        assert result.winner_id == gid1
        assert result.loser_id == gid2


# ============================================================
# Leaderboard: Edge Cases
# ============================================================

class TestLeaderboardEdgeCases:
    def test_pvp_win_streak_resets_on_loss(self):
        gid = _make_game("Alice")
        record_pvp_result(gid, won=True)
        record_pvp_result(gid, won=True)
        record_pvp_result(gid, won=False)  # Reset
        record_pvp_result(gid, won=True)
        stats = _player_stats[gid]
        assert stats["pvp_win_streak"] == 1
        assert stats["max_pvp_win_streak"] == 2

    def test_achievement_speed_demon_not_awarded_slow(self):
        gid = _make_game("Alice")
        _earned_badges[gid] = {"boulder"}
        _games[gid]["play_time_seconds"] = 2000  # 33 min > 30 min
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "speed_demon" not in earned_ids
        _earned_badges.pop(gid, None)

    def test_achievement_no_game_returns_empty(self):
        result = check_achievements("nonexistent")
        assert result.newly_earned == []

    def test_multiple_badges_multiple_achievements(self):
        gid = _make_game("Alice")
        _earned_badges[gid] = {"boulder", "cascade"}
        result = check_achievements(gid)
        earned_ids = [a.id for a in result.newly_earned]
        assert "rock_solid" in earned_ids
        assert "water_works" in earned_ids
        _earned_badges.pop(gid, None)


# ============================================================
# API Integration Tests (FastAPI TestClient)
# ============================================================

class TestTradeAPI:
    def test_create_trade_api(self):
        gid = _make_game("Alice")
        resp = client.post("/api/trade/create", json={"player_id": gid})
        assert resp.status_code == 200
        data = resp.json()
        assert "session" in data
        assert data["session"]["status"] == "waiting"

    def test_create_trade_invalid_game(self):
        resp = client.post("/api/trade/create", json={"player_id": "bad"})
        assert resp.status_code == 400

    def test_trade_history_api(self):
        resp = client.get("/api/trade/history/nobody")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_delete_trade_session_api(self):
        gid = _make_game("Alice")
        resp = client.post("/api/trade/create", json={"player_id": gid})
        sid = resp.json()["session"]["id"]
        resp2 = client.delete(f"/api/trade/session/{sid}")
        assert resp2.status_code == 200

    def test_delete_nonexistent_session(self):
        resp = client.delete("/api/trade/session/nope")
        assert resp.status_code == 404


class TestPvPAPI:
    def test_create_pvp_api(self):
        gid = _make_game("Alice")
        resp = client.post("/api/pvp/create", json={"player_id": gid})
        assert resp.status_code == 200
        assert "session" in resp.json()

    def test_pvp_history_api(self):
        resp = client.get("/api/pvp/history/nobody")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_pvp_session_not_found(self):
        resp = client.get("/api/pvp/session/nope")
        assert resp.status_code == 404


class TestLeaderboardAPI:
    def test_trainer_leaderboard_api(self):
        resp = client.get("/api/leaderboard/trainers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_pvp_leaderboard_api(self):
        resp = client.get("/api/leaderboard/pvp")
        assert resp.status_code == 200

    def test_pokedex_leaderboard_api(self):
        resp = client.get("/api/leaderboard/pokedex")
        assert resp.status_code == 200

    def test_player_stats_api(self):
        gid = _make_game("Alice")
        resp = client.get(f"/api/player/{gid}/stats")
        assert resp.status_code == 200
        assert resp.json()["player_name"] == "Alice"

    def test_player_stats_not_found(self):
        resp = client.get("/api/player/nope/stats")
        assert resp.status_code == 404

    def test_achievements_api(self):
        gid = _make_game("Alice")
        resp = client.get(f"/api/player/{gid}/achievements")
        assert resp.status_code == 200
        assert len(resp.json()) == 35

    def test_check_achievements_api(self):
        gid = _make_game("Alice")
        record_pokemon_caught(gid)
        resp = client.post(f"/api/achievements/check/{gid}")
        assert resp.status_code == 200
        earned_ids = [a["id"] for a in resp.json()["newly_earned"]]
        assert "first_steps" in earned_ids

    def test_leaderboard_limit_param(self):
        resp = client.get("/api/leaderboard/trainers?limit=1")
        assert resp.status_code == 200
        assert len(resp.json()) <= 1
