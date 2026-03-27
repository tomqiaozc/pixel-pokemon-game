"""Tests for the multiplayer PvP battle system."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.models.pvp import PvPAction, PvPBattleResult, PvPSession, PvPTurnResult
from backend.services.game_service import create_game
from backend.services.pvp_service import (
    _pvp_actions,
    _pvp_battles,
    _pvp_codes,
    _pvp_history,
    _pvp_results,
    _pvp_sessions,
    _pvp_turn_results,
    cancel_pvp_session,
    create_pvp_session,
    forfeit_battle,
    get_pvp_history,
    get_pvp_session,
    join_pvp_session,
    ready_up,
    start_pvp_battle,
    submit_action,
)


@pytest.fixture(autouse=True)
def _clean_pvp_state():
    """Clear PvP state between tests."""
    _pvp_sessions.clear()
    _pvp_codes.clear()
    _pvp_battles.clear()
    _pvp_actions.clear()
    _pvp_turn_results.clear()
    _pvp_history.clear()
    _pvp_results.clear()
    yield
    _pvp_sessions.clear()
    _pvp_codes.clear()
    _pvp_battles.clear()
    _pvp_actions.clear()
    _pvp_turn_results.clear()
    _pvp_history.clear()
    _pvp_results.clear()


def _create_game_with_team(name: str) -> str:
    """Helper: create a game with a team of 3 Pokemon."""
    game = create_game(name, 1)
    game_id = game["id"]
    game["player"]["team"].append({
        "id": 4, "name": "Charmander", "types": ["fire"],
        "stats": {"hp": 100, "attack": 100, "defense": 100, "sp_attack": 100, "sp_defense": 100, "speed": 100},
        "moves": [{"name": "Ember", "type": "fire", "power": 40, "accuracy": 100, "pp": 25}],
        "sprite": "test.png", "level": 10,
    })
    game["player"]["team"].append({
        "id": 7, "name": "Squirtle", "types": ["water"],
        "stats": {"hp": 100, "attack": 100, "defense": 100, "sp_attack": 100, "sp_defense": 100, "speed": 100},
        "moves": [{"name": "Water Gun", "type": "water", "power": 40, "accuracy": 100, "pp": 25}],
        "sprite": "test.png", "level": 10,
    })
    return game_id


def _setup_battle():
    """Helper: create two games, create/join/ready/start a PvP battle."""
    gid1 = _create_game_with_team("Alice")
    gid2 = _create_game_with_team("Bob")
    session = create_pvp_session(gid1)
    join_pvp_session(session.battle_code, gid2)
    ready_up(session.id, gid1)
    ready_up(session.id, gid2)
    battle = start_pvp_battle(session.id)
    return gid1, gid2, session, battle


# ============================================================
# Session Creation
# ============================================================

class TestCreatePvPSession:
    def test_create_session(self):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        assert isinstance(session, PvPSession)
        assert session.player1_id == gid
        assert session.status == "waiting"
        assert len(session.battle_code) == 6

    def test_create_invalid_game(self):
        with pytest.raises(ValueError, match="Game not found"):
            create_pvp_session("nonexistent")

    def test_session_retrievable(self):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        assert get_pvp_session(session.id) is not None


# ============================================================
# Joining Sessions
# ============================================================

class TestJoinPvPSession:
    def test_join_session(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        joined = join_pvp_session(session.battle_code, gid2)
        assert joined.player2_id == gid2
        assert joined.status == "ready"

    def test_join_invalid_code(self):
        gid = _create_game_with_team("Bob")
        with pytest.raises(ValueError, match="Invalid battle code"):
            join_pvp_session("XXXXXX", gid)

    def test_join_own_session(self):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        with pytest.raises(ValueError, match="Cannot join your own"):
            join_pvp_session(session.battle_code, gid)

    def test_join_full_session(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        gid3 = _create_game_with_team("Charlie")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        with pytest.raises(ValueError, match="full"):
            join_pvp_session(session.battle_code, gid3)


# ============================================================
# Ready Up & Battle Start
# ============================================================

class TestReadyAndStart:
    def test_ready_up(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        updated = ready_up(session.id, gid1)
        assert updated.player1_ready is True
        assert updated.player2_ready is False

    def test_ready_before_join_fails(self):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        with pytest.raises(ValueError, match="Both players must join"):
            ready_up(session.id, gid)

    def test_start_battle(self):
        gid1, gid2, session, battle = _setup_battle()
        assert battle is not None
        assert battle.battle_type == "pvp"
        assert battle.can_run is False
        assert session.status == "battling"

    def test_start_requires_both_ready(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        ready_up(session.id, gid1)
        with pytest.raises(ValueError, match="Both players must be ready"):
            start_pvp_battle(session.id)


# ============================================================
# Turn Actions
# ============================================================

class TestTurnActions:
    def test_single_action_waits(self):
        gid1, gid2, session, battle = _setup_battle()
        action = PvPAction(action="fight", move_index=0)
        result = submit_action(session.id, gid1, action)
        assert result["status"] == "waiting_for_opponent"

    def test_both_actions_resolves(self):
        gid1, gid2, session, battle = _setup_battle()
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        result = submit_action(session.id, gid2, a2)
        assert result["status"] == "turn_resolved"
        assert "result" in result
        turn_result = result["result"]
        assert isinstance(turn_result, PvPTurnResult)
        assert turn_result.turn_number == 1

    def test_invalid_move_index(self):
        gid1, gid2, session, battle = _setup_battle()
        action = PvPAction(action="fight", move_index=99)
        with pytest.raises(ValueError, match="Invalid move index"):
            submit_action(session.id, gid1, action)

    def test_non_participant_rejected(self):
        gid1, gid2, session, battle = _setup_battle()
        gid3 = _create_game_with_team("Charlie")
        action = PvPAction(action="fight", move_index=0)
        with pytest.raises(ValueError, match="Player not in this session"):
            submit_action(session.id, gid3, action)

    def test_multiple_turns(self):
        gid1, gid2, session, battle = _setup_battle()
        for turn in range(3):
            a1 = PvPAction(action="fight", move_index=0)
            a2 = PvPAction(action="fight", move_index=0)
            submit_action(session.id, gid1, a1)
            result = submit_action(session.id, gid2, a2)
            if result["status"] == "turn_resolved" and result["result"].battle_over:
                break


# ============================================================
# Forfeit
# ============================================================

class TestForfeit:
    def test_forfeit(self):
        gid1, gid2, session, battle = _setup_battle()
        result = forfeit_battle(session.id, gid1)
        assert isinstance(result, PvPBattleResult)
        assert result.winner_id == gid2
        assert result.loser_id == gid1
        assert result.forfeit is True

    def test_forfeit_records_history(self):
        gid1, gid2, session, battle = _setup_battle()
        forfeit_battle(session.id, gid1)
        h1 = get_pvp_history(gid1)
        h2 = get_pvp_history(gid2)
        assert len(h1) == 1
        assert h1[0].result == "loss"
        assert h1[0].forfeit is True
        assert len(h2) == 1
        assert h2[0].result == "win"

    def test_forfeit_non_battling_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        with pytest.raises(ValueError, match="No active battle"):
            forfeit_battle(session.id, gid1)


# ============================================================
# Cancel
# ============================================================

class TestCancel:
    def test_cancel_session(self):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        assert cancel_pvp_session(session.id) is True
        assert get_pvp_session(session.id) is None

    def test_cancel_nonexistent(self):
        assert cancel_pvp_session("nope") is False


# ============================================================
# Battle Resolution
# ============================================================

class TestBattleResolution:
    def test_battle_ends_with_winner(self):
        """Run turns until battle ends — one player should win."""
        gid1, gid2, session, battle = _setup_battle()
        for _ in range(100):  # Safety limit
            a1 = PvPAction(action="fight", move_index=0)
            a2 = PvPAction(action="fight", move_index=0)
            submit_action(session.id, gid1, a1)
            result = submit_action(session.id, gid2, a2)
            if result["status"] == "turn_resolved" and result["result"].battle_over:
                assert result["result"].winner in ("player1", "player2")
                return
        pytest.fail("Battle did not end within 100 turns")

    def test_history_recorded_after_battle(self):
        """Run a battle to completion and check history."""
        gid1, gid2, session, battle = _setup_battle()
        for _ in range(100):
            a1 = PvPAction(action="fight", move_index=0)
            a2 = PvPAction(action="fight", move_index=0)
            submit_action(session.id, gid1, a1)
            result = submit_action(session.id, gid2, a2)
            if result["status"] == "turn_resolved" and result["result"].battle_over:
                break
        h1 = get_pvp_history(gid1)
        h2 = get_pvp_history(gid2)
        assert len(h1) == 1
        assert len(h2) == 1
        # One should win, other should lose
        results = {h1[0].result, h2[0].result}
        assert results == {"win", "loss"}


# ============================================================
# History
# ============================================================

class TestHistory:
    def test_empty_history(self):
        assert get_pvp_history("nobody") == []
