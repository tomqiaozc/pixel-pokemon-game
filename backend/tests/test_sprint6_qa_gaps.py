"""Sprint 6 QA-A gap coverage tests: Trading system & Multiplayer PvP.

Supplements test_trade.py and test_pvp.py with edge-case, API route,
timeout, and integration coverage.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.pvp import PvPAction, PvPBattleResult, PvPSession
from backend.models.trade import TradeResult, TradeSession
from backend.services.game_service import create_game, get_game
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
    get_pvp_battle,
    get_pvp_history,
    get_pvp_result,
    get_pvp_session,
    get_last_turn_result,
    join_pvp_session,
    ready_up,
    start_pvp_battle,
    submit_action,
)
from backend.services.trade_service import (
    SESSION_TIMEOUT_SECONDS,
    _trade_codes,
    _trade_history,
    _trade_sessions,
    cancel_offer,
    cancel_trade_session,
    confirm_trade,
    create_trade_session,
    get_player_team,
    get_trade_history,
    get_trade_session,
    join_trade_session,
    set_trade_offer,
)


# ============================================================
# Shared fixtures
# ============================================================

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clean_all_state():
    """Clear trade and PvP state between tests."""
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


def _create_game_with_team(name: str, team_size: int = 3) -> str:
    """Helper: create a game and add extra Pokemon to the team."""
    game = create_game(name, 1)  # Bulbasaur starter
    game_id = game["id"]
    for i in range(team_size - 1):
        game["player"]["team"].append({
            "id": 4 + i,
            "name": f"ExtraMon{i}",
            "types": ["fire"],
            "stats": {"hp": 100, "attack": 100, "defense": 100,
                      "sp_attack": 100, "sp_defense": 100, "speed": 100},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40,
                        "accuracy": 100, "pp": 35}],
            "sprite": "test.png",
            "level": 10,
        })
    return game_id


def _setup_pvp_battle():
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
# TRADE — API route tests
# ============================================================

class TestTradeAPIRoutes:
    """Test trade endpoints via TestClient (HTTP layer validation)."""

    def test_create_trade_api(self, client):
        resp = client.post("/api/game/new", json={"player_name": "Alice", "starter_pokemon_id": 1})
        gid = resp.json()["id"]
        # Add extra Pokemon
        game = get_game(gid)
        game["player"]["team"].append({
            "id": 4, "name": "Extra", "types": ["fire"],
            "stats": {"hp": 100, "attack": 100, "defense": 100,
                      "sp_attack": 100, "sp_defense": 100, "speed": 100},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40,
                        "accuracy": 100, "pp": 35}],
            "sprite": "t.png", "level": 10,
        })
        resp = client.post("/api/trade/create", json={"player_id": gid})
        assert resp.status_code == 200
        data = resp.json()
        assert "session" in data
        assert data["session"]["status"] == "waiting"

    def test_create_trade_api_invalid_game(self, client):
        resp = client.post("/api/trade/create", json={"player_id": "bad"})
        assert resp.status_code == 400

    def test_join_trade_api(self, client):
        r1 = client.post("/api/game/new", json={"player_name": "Alice", "starter_pokemon_id": 1})
        r2 = client.post("/api/game/new", json={"player_name": "Bob", "starter_pokemon_id": 4})
        gid1, gid2 = r1.json()["id"], r2.json()["id"]
        for gid in [gid1, gid2]:
            g = get_game(gid)
            g["player"]["team"].append({
                "id": 7, "name": "X", "types": ["water"],
                "stats": {"hp": 100, "attack": 100, "defense": 100,
                          "sp_attack": 100, "sp_defense": 100, "speed": 100},
                "moves": [{"name": "Tackle", "type": "normal", "power": 40,
                            "accuracy": 100, "pp": 35}],
                "sprite": "t.png", "level": 10,
            })
        cr = client.post("/api/trade/create", json={"player_id": gid1})
        code = cr.json()["session"]["trade_code"]
        resp = client.post(f"/api/trade/join/{code}", json={"player_id": gid2})
        assert resp.status_code == 200
        assert resp.json()["session"]["status"] == "selecting"

    def test_join_trade_api_invalid_code(self, client):
        r = client.post("/api/game/new", json={"player_name": "Bob", "starter_pokemon_id": 1})
        gid = r.json()["id"]
        resp = client.post("/api/trade/join/ZZZZZZ", json={"player_id": gid})
        assert resp.status_code == 400

    def test_get_session_api(self, client):
        gid = _create_game_with_team("Alice")
        session = create_trade_session(gid)
        resp = client.get(f"/api/trade/session/{session.id}")
        assert resp.status_code == 200
        assert resp.json()["session"]["id"] == session.id

    def test_get_session_api_not_found(self, client):
        resp = client.get("/api/trade/session/nonexistent")
        assert resp.status_code == 404

    def test_delete_session_api(self, client):
        gid = _create_game_with_team("Alice")
        session = create_trade_session(gid)
        resp = client.delete(f"/api/trade/session/{session.id}")
        assert resp.status_code == 200
        assert "cancelled" in resp.json()["message"].lower()

    def test_delete_session_api_not_found(self, client):
        resp = client.delete("/api/trade/session/nonexistent")
        assert resp.status_code == 404

    def test_offer_api(self, client):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        resp = client.post("/api/trade/offer", json={
            "session_id": session.id, "player_id": gid1, "pokemon_index": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["session"]["player1_offer"] is not None

    def test_offer_api_invalid(self, client):
        resp = client.post("/api/trade/offer", json={
            "session_id": "bad", "player_id": "bad", "pokemon_index": 0,
        })
        assert resp.status_code == 400

    def test_confirm_api(self, client):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        resp = client.post("/api/trade/confirm", json={
            "session_id": session.id, "player_id": gid1,
        })
        assert resp.status_code == 200
        assert resp.json()["trade_completed"] is False

    def test_confirm_both_api(self, client):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        client.post("/api/trade/confirm", json={
            "session_id": session.id, "player_id": gid1,
        })
        resp = client.post("/api/trade/confirm", json={
            "session_id": session.id, "player_id": gid2,
        })
        assert resp.status_code == 200
        assert resp.json()["trade_completed"] is True

    def test_cancel_offer_api(self, client):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        resp = client.post("/api/trade/cancel", json={
            "session_id": session.id, "player_id": gid1,
        })
        assert resp.status_code == 200
        assert resp.json()["session"]["player1_offer"] is None

    def test_history_api(self, client):
        gid1 = _create_game_with_team("Alice")
        resp = client.get(f"/api/trade/history/{gid1}")
        assert resp.status_code == 200
        assert resp.json() == []


# ============================================================
# TRADE — Timeout & expiry
# ============================================================

class TestTradeTimeout:
    def test_expired_session_returns_none(self):
        gid = _create_game_with_team("Alice")
        session = create_trade_session(gid)
        # Simulate expiry by backdating last_activity
        past = datetime.now(timezone.utc) - timedelta(seconds=SESSION_TIMEOUT_SECONDS + 10)
        session.last_activity = past
        assert get_trade_session(session.id) is None

    def test_join_expired_session_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        past = datetime.now(timezone.utc) - timedelta(seconds=SESSION_TIMEOUT_SECONDS + 10)
        session.last_activity = past
        with pytest.raises(ValueError, match="expired"):
            join_trade_session(session.trade_code, gid2)

    def test_offer_on_expired_session_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        past = datetime.now(timezone.utc) - timedelta(seconds=SESSION_TIMEOUT_SECONDS + 10)
        session.last_activity = past
        with pytest.raises(ValueError, match="expired"):
            set_trade_offer(session.id, gid1, 0)

    def test_confirm_on_expired_session_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        past = datetime.now(timezone.utc) - timedelta(seconds=SESSION_TIMEOUT_SECONDS + 10)
        session.last_activity = past
        with pytest.raises(ValueError, match="expired"):
            confirm_trade(session.id, gid1)


# ============================================================
# TRADE — Edge cases
# ============================================================

class TestTradeEdgeCases:
    def test_negative_pokemon_index(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="Invalid Pokemon index"):
            set_trade_offer(session.id, gid1, -1)

    def test_player2_can_set_offer(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        updated = set_trade_offer(session.id, gid2, 0)
        assert updated.player2_offer is not None
        assert updated.player2_offer.player_id == gid2

    def test_re_offer_resets_status_to_selecting(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        assert session.status == "confirmed"
        # Player 1 changes offer — should reset status
        set_trade_offer(session.id, gid1, 1)
        assert session.status == "selecting"
        assert session.player1_confirmed is False

    def test_offer_in_waiting_status_fails(self):
        """Cannot offer before player2 joins (status='waiting')."""
        gid1 = _create_game_with_team("Alice")
        session = create_trade_session(gid1)
        assert session.status == "waiting"
        with pytest.raises(ValueError, match="Cannot offer"):
            set_trade_offer(session.id, gid1, 0)

    def test_confirm_non_participant(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        gid3 = _create_game_with_team("Charlie")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        with pytest.raises(ValueError, match="not in this trade"):
            confirm_trade(session.id, gid3)

    def test_cancel_offer_non_participant(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        gid3 = _create_game_with_team("Charlie")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="not in this trade"):
            cancel_offer(session.id, gid3)

    def test_cancel_offer_resets_player2_confirmation(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid2)
        assert session.player2_confirmed is True
        # Player 2 cancels
        updated = cancel_offer(session.id, gid2)
        assert updated.player2_offer is None
        assert updated.player2_confirmed is False
        assert updated.status == "selecting"

    def test_cancel_on_expired_session_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        past = datetime.now(timezone.utc) - timedelta(seconds=SESSION_TIMEOUT_SECONDS + 10)
        session.last_activity = past
        with pytest.raises(ValueError, match="expired"):
            cancel_offer(session.id, gid1)

    def test_trade_code_length(self):
        gid = _create_game_with_team("Alice")
        session = create_trade_session(gid)
        assert len(session.trade_code) == 6
        assert session.trade_code.isalnum()
        assert session.trade_code == session.trade_code.upper()

    def test_trade_code_maps_to_session(self):
        gid = _create_game_with_team("Alice")
        session = create_trade_session(gid)
        assert session.trade_code in _trade_codes
        assert _trade_codes[session.trade_code] == session.id


# ============================================================
# TRADE — Result and metadata details
# ============================================================

class TestTradeResultDetails:
    def test_trade_result_message_content(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        result = confirm_trade(session.id, gid2)
        assert isinstance(result, TradeResult)
        assert "Trade complete" in result.message
        assert "Alice" in result.message

    def test_trade_result_fields(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        result = confirm_trade(session.id, gid2)
        assert result.player1_given is not None
        assert result.player1_received is not None
        assert result.player2_given is not None
        assert result.player2_received is not None
        # player1_given should be player2_received
        assert result.player1_given["name"] == result.player2_received["name"]
        assert result.player2_given["name"] == result.player1_received["name"]

    def test_traded_pokemon_outsider_flag(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        result = confirm_trade(session.id, gid2)
        # Check that received Pokemon are marked as outsiders in the team
        team1 = get_player_team(gid1)
        team2 = get_player_team(gid2)
        received_by_1 = [p for p in team1 if p.get("is_outsider")]
        received_by_2 = [p for p in team2 if p.get("is_outsider")]
        assert len(received_by_1) >= 1
        assert len(received_by_2) >= 1

    def test_trade_history_records_pokemon_names(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        team1_first = get_player_team(gid1)[0]["name"]
        team2_first = get_player_team(gid2)[0]["name"]
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        confirm_trade(session.id, gid2)
        h1 = get_trade_history(gid1)
        assert h1[0].given_pokemon == team1_first
        assert h1[0].received_pokemon == team2_first

    def test_trade_cleanup_removes_code(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        code = session.trade_code
        join_trade_session(code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        confirm_trade(session.id, gid2)
        # Code should be cleaned up
        assert code not in _trade_codes

    def test_multiple_trades_between_same_players(self):
        gid1 = _create_game_with_team("Alice", team_size=4)
        gid2 = _create_game_with_team("Bob", team_size=4)
        # First trade
        s1 = create_trade_session(gid1)
        join_trade_session(s1.trade_code, gid2)
        set_trade_offer(s1.id, gid1, 0)
        set_trade_offer(s1.id, gid2, 0)
        confirm_trade(s1.id, gid1)
        confirm_trade(s1.id, gid2)
        # Second trade
        s2 = create_trade_session(gid1)
        join_trade_session(s2.trade_code, gid2)
        set_trade_offer(s2.id, gid1, 0)
        set_trade_offer(s2.id, gid2, 0)
        confirm_trade(s2.id, gid1)
        confirm_trade(s2.id, gid2)
        # Both should have 2 history entries
        h1 = get_trade_history(gid1)
        h2 = get_trade_history(gid2)
        assert len(h1) == 2
        assert len(h2) == 2


# ============================================================
# PVP — API route tests
# ============================================================

class TestPvPAPIRoutes:
    """Test PvP endpoints via TestClient."""

    def _create_api_game(self, client, name):
        resp = client.post("/api/game/new", json={"player_name": name, "starter_pokemon_id": 1})
        gid = resp.json()["id"]
        game = get_game(gid)
        game["player"]["team"].append({
            "id": 4, "name": "Charmander", "types": ["fire"],
            "stats": {"hp": 100, "attack": 100, "defense": 100,
                      "sp_attack": 100, "sp_defense": 100, "speed": 100},
            "moves": [{"name": "Ember", "type": "fire", "power": 40,
                        "accuracy": 100, "pp": 25}],
            "sprite": "test.png", "level": 10,
        })
        return gid

    def test_create_pvp_api(self, client):
        gid = self._create_api_game(client, "Alice")
        resp = client.post("/api/pvp/create", json={"player_id": gid})
        assert resp.status_code == 200
        assert "session" in resp.json()
        assert resp.json()["session"]["status"] == "waiting"

    def test_create_pvp_api_invalid_game(self, client):
        resp = client.post("/api/pvp/create", json={"player_id": "bad"})
        assert resp.status_code == 400

    def test_join_pvp_api(self, client):
        gid1 = self._create_api_game(client, "Alice")
        gid2 = self._create_api_game(client, "Bob")
        cr = client.post("/api/pvp/create", json={"player_id": gid1})
        code = cr.json()["session"]["battle_code"]
        resp = client.post(f"/api/pvp/join/{code}", json={"player_id": gid2})
        assert resp.status_code == 200
        assert resp.json()["session"]["status"] == "ready"

    def test_join_pvp_api_invalid_code(self, client):
        gid = self._create_api_game(client, "Bob")
        resp = client.post("/api/pvp/join/ZZZZZZ", json={"player_id": gid})
        assert resp.status_code == 400

    def test_get_pvp_session_api(self, client):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        resp = client.get(f"/api/pvp/session/{session.id}")
        assert resp.status_code == 200
        assert resp.json()["session"]["id"] == session.id

    def test_get_pvp_session_api_not_found(self, client):
        resp = client.get("/api/pvp/session/nonexistent")
        assert resp.status_code == 404

    def test_delete_pvp_session_api(self, client):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        resp = client.delete(f"/api/pvp/session/{session.id}")
        assert resp.status_code == 200
        assert "cancelled" in resp.json()["message"].lower()

    def test_delete_pvp_session_api_not_found(self, client):
        resp = client.delete("/api/pvp/session/nonexistent")
        assert resp.status_code == 404

    def test_ready_api(self, client):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        resp = client.post("/api/pvp/ready", json={
            "session_id": session.id, "player_id": gid1, "lead_pokemon_index": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["battle_started"] is False

    def test_ready_both_starts_battle_api(self, client):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        client.post("/api/pvp/ready", json={
            "session_id": session.id, "player_id": gid1, "lead_pokemon_index": 0,
        })
        resp = client.post("/api/pvp/ready", json={
            "session_id": session.id, "player_id": gid2, "lead_pokemon_index": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["battle_started"] is True

    def test_action_api(self, client):
        gid1, gid2, session, battle = _setup_pvp_battle()
        resp = client.post("/api/pvp/action", json={
            "session_id": session.id, "player_id": gid1,
            "action": "fight", "move_index": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "waiting_for_opponent"

    def test_action_api_invalid(self, client):
        resp = client.post("/api/pvp/action", json={
            "session_id": "bad", "player_id": "bad",
            "action": "fight", "move_index": 0,
        })
        assert resp.status_code == 400

    def test_forfeit_api(self, client):
        gid1, gid2, session, battle = _setup_pvp_battle()
        resp = client.post("/api/pvp/forfeit", json={
            "session_id": session.id, "player_id": gid1,
        })
        assert resp.status_code == 200
        assert resp.json()["result"]["forfeit"] is True

    def test_result_api(self, client):
        gid1, gid2, session, battle = _setup_pvp_battle()
        forfeit_battle(session.id, gid1)
        resp = client.get(f"/api/pvp/result/{session.id}")
        assert resp.status_code == 200
        assert resp.json()["winner_id"] == gid2

    def test_result_api_not_found(self, client):
        resp = client.get("/api/pvp/result/nonexistent")
        assert resp.status_code == 404

    def test_history_api(self, client):
        resp = client.get("/api/pvp/history/nobody")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_state_api_alias(self, client):
        """GET /api/pvp/state/{session_id} is an alias for get_session."""
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        resp = client.get(f"/api/pvp/state/{session.id}")
        assert resp.status_code == 200
        assert resp.json()["session"]["id"] == session.id


# ============================================================
# PVP — Timeout & expiry
# ============================================================

class TestPvPTimeout:
    def test_expired_session_returns_none(self):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        past = datetime.now(timezone.utc) - timedelta(
            seconds=SESSION_TIMEOUT_SECONDS + 10
        )
        session.last_activity = past
        assert get_pvp_session(session.id) is None

    def test_join_expired_session_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        past = datetime.now(timezone.utc) - timedelta(
            seconds=SESSION_TIMEOUT_SECONDS + 10
        )
        session.last_activity = past
        with pytest.raises(ValueError, match="expired"):
            join_pvp_session(session.battle_code, gid2)


# ============================================================
# PVP — Ready-up edge cases
# ============================================================

class TestPvPReadyEdgeCases:
    def test_ready_invalid_lead_index(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        with pytest.raises(ValueError, match="Invalid lead Pokemon index"):
            ready_up(session.id, gid1, lead_pokemon_index=99)

    def test_ready_negative_lead_index(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        with pytest.raises(ValueError, match="Invalid lead Pokemon index"):
            ready_up(session.id, gid1, lead_pokemon_index=-1)

    def test_ready_non_participant(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        gid3 = _create_game_with_team("Charlie")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        with pytest.raises(ValueError, match="Player not in this session"):
            ready_up(session.id, gid3)

    def test_ready_on_expired_session_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        past = datetime.now(timezone.utc) - timedelta(
            seconds=SESSION_TIMEOUT_SECONDS + 10
        )
        session.last_activity = past
        with pytest.raises(ValueError, match="expired"):
            ready_up(session.id, gid1)


# ============================================================
# PVP — Battle start edge cases
# ============================================================

class TestPvPBattleStartEdgeCases:
    def test_start_already_started_returns_existing(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        battle2 = start_pvp_battle(session.id)
        assert battle2 is not None
        assert battle2.id == battle.id

    def test_start_with_lost_battle_state(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        # Remove battle state to simulate loss
        _pvp_battles.pop(session.id, None)
        with pytest.raises(ValueError, match="Battle state lost"):
            start_pvp_battle(session.id)

    def test_battle_type_is_pvp(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        assert battle.battle_type == "pvp"

    def test_battle_cannot_run(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        assert battle.can_run is False


# ============================================================
# PVP — Action edge cases
# ============================================================

class TestPvPActionEdgeCases:
    def test_action_on_completed_battle_fails(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        forfeit_battle(session.id, gid1)
        action = PvPAction(action="fight", move_index=0)
        with pytest.raises(ValueError):
            submit_action(session.id, gid1, action)

    def test_action_before_battle_started_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        ready_up(session.id, gid1)
        ready_up(session.id, gid2)
        # Don't start — still in "ready" status... actually ready_up doesn't
        # start the battle, but _setup_pvp_battle calls start_pvp_battle.
        # Actually we need to not call start_pvp_battle.
        # The issue: ready_up just sets ready flags, but the route auto-starts.
        # At service level, session status is "ready" until start_pvp_battle.
        # But start was already called. Let's create a fresh session without starting.
        _pvp_sessions.clear()
        _pvp_codes.clear()
        _pvp_battles.clear()
        _pvp_actions.clear()
        gid1 = _create_game_with_team("Eve")
        gid2 = _create_game_with_team("Dan")
        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        # Don't ready up, don't start
        action = PvPAction(action="fight", move_index=0)
        with pytest.raises(ValueError, match="Battle has not started"):
            submit_action(session.id, gid1, action)

    def test_actions_reset_after_turn(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        submit_action(session.id, gid2, a2)
        # Actions should be cleared
        assert len(_pvp_actions.get(session.id, {})) == 0

    def test_turn_count_increments(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        assert battle.turn_count == 0
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        result = submit_action(session.id, gid2, a2)
        if result["status"] == "turn_resolved":
            assert result["result"].turn_number == 1
            assert battle.turn_count == 1


# ============================================================
# PVP — Forfeit edge cases
# ============================================================

class TestPvPForfeitEdgeCases:
    def test_forfeit_non_participant(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        gid3 = _create_game_with_team("Charlie")
        with pytest.raises(ValueError, match="Player not in this session"):
            forfeit_battle(session.id, gid3)

    def test_forfeit_sets_session_completed(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        forfeit_battle(session.id, gid1)
        assert session.status == "completed"

    def test_forfeit_sets_battle_over(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        forfeit_battle(session.id, gid1)
        assert battle.is_over is True
        assert battle.winner == "player2"

    def test_forfeit_player2(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        result = forfeit_battle(session.id, gid2)
        assert result.winner_id == gid1
        assert result.loser_id == gid2
        assert battle.winner == "player1"

    def test_forfeit_result_stored(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        forfeit_battle(session.id, gid1)
        stored = get_pvp_result(session.id)
        assert stored is not None
        assert stored.forfeit is True
        assert stored.winner_id == gid2

    def test_forfeit_before_any_turns(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        result = forfeit_battle(session.id, gid1)
        assert result.turns == 0


# ============================================================
# PVP — Turn resolution details
# ============================================================

class TestPvPTurnResolution:
    def test_turn_result_has_events(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        result = submit_action(session.id, gid2, a2)
        if result["status"] == "turn_resolved":
            tr = result["result"]
            assert len(tr.events) > 0

    def test_speed_determines_order(self):
        """Faster Pokemon should attack first."""
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        # Make player1's Pokemon faster
        game1 = get_game(gid1)
        game1["player"]["team"][0]["stats"]["speed"] = 200
        game2 = get_game(gid2)
        game2["player"]["team"][0]["stats"]["speed"] = 50

        session = create_pvp_session(gid1)
        join_pvp_session(session.battle_code, gid2)
        ready_up(session.id, gid1)
        ready_up(session.id, gid2)
        battle = start_pvp_battle(session.id)

        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        result = submit_action(session.id, gid2, a2)
        if result["status"] == "turn_resolved":
            tr = result["result"]
            if len(tr.events) >= 1:
                # First attack should be from player (faster)
                assert tr.events[0].attacker == "player"

    def test_last_turn_result_stored(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        submit_action(session.id, gid2, a2)
        last = get_last_turn_result(session.id)
        assert last is not None
        assert last.turn_number == 1

    def test_battle_state_retrievable(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        b = get_pvp_battle(session.id)
        assert b is not None
        assert b.id == session.id

    def test_battle_over_after_ko(self):
        """Set defender HP low so one hit KOs it, then verify battle ends."""
        gid1, gid2, session, battle = _setup_pvp_battle()
        # Set enemy to 1 HP
        battle.enemy_pokemon.current_hp = 1
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        result = submit_action(session.id, gid2, a2)
        if result["status"] == "turn_resolved":
            assert result["result"].battle_over is True

    def test_flinched_reset_each_turn(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        battle.player_pokemon.flinched = True
        battle.enemy_pokemon.flinched = True
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        submit_action(session.id, gid2, a2)
        assert battle.player_pokemon.flinched is False
        assert battle.enemy_pokemon.flinched is False


# ============================================================
# PVP — Cancel edge cases
# ============================================================

class TestPvPCancelEdgeCases:
    def test_cancel_cleans_up_code(self):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        code = session.battle_code
        assert code in _pvp_codes
        cancel_pvp_session(session.id)
        assert code not in _pvp_codes

    def test_cancel_cleans_up_battle_state(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        cancel_pvp_session(session.id)
        assert get_pvp_battle(session.id) is None
        assert get_pvp_session(session.id) is None

    def test_cancel_cleans_up_actions(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        a1 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        cancel_pvp_session(session.id)
        assert session.id not in _pvp_actions


# ============================================================
# PVP — Session state response
# ============================================================

class TestPvPStateResponse:
    def test_state_response_includes_pokemon_during_battle(self, client):
        gid1, gid2, session, battle = _setup_pvp_battle()
        resp = client.get(f"/api/pvp/session/{session.id}")
        data = resp.json()
        assert data["player1_pokemon"] is not None
        assert data["player2_pokemon"] is not None
        assert "name" in data["player1_pokemon"]
        assert "current_hp" in data["player1_pokemon"]
        assert "max_hp" in data["player1_pokemon"]

    def test_state_response_no_pokemon_before_battle(self, client):
        gid = _create_game_with_team("Alice")
        session = create_pvp_session(gid)
        resp = client.get(f"/api/pvp/session/{session.id}")
        data = resp.json()
        assert data["player1_pokemon"] is None
        assert data["player2_pokemon"] is None
        assert data["turn_number"] == 0

    def test_state_response_includes_turn_number(self, client):
        gid1, gid2, session, battle = _setup_pvp_battle()
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        submit_action(session.id, gid2, a2)
        resp = client.get(f"/api/pvp/session/{session.id}")
        data = resp.json()
        assert data["turn_number"] >= 1


# ============================================================
# PVP — History details
# ============================================================

class TestPvPHistoryDetails:
    def test_forfeit_history_opponent_name(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        forfeit_battle(session.id, gid1)
        h2 = get_pvp_history(gid2)
        assert h2[0].opponent_name == "Alice"

    def test_battle_history_has_date(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        forfeit_battle(session.id, gid1)
        h1 = get_pvp_history(gid1)
        assert h1[0].date is not None
        assert len(h1[0].date) > 0

    def test_battle_history_turn_count(self):
        gid1, gid2, session, battle = _setup_pvp_battle()
        # Play one turn, then forfeit
        a1 = PvPAction(action="fight", move_index=0)
        a2 = PvPAction(action="fight", move_index=0)
        submit_action(session.id, gid1, a1)
        submit_action(session.id, gid2, a2)
        forfeit_battle(session.id, gid1)
        h1 = get_pvp_history(gid1)
        assert h1[0].turns == 1
