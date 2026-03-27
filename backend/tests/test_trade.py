"""Tests for the Pokemon trading system."""
from __future__ import annotations

import pytest

from backend.models.trade import TradeResult, TradeSession
from backend.services.game_service import create_game
from backend.services.trade_service import (
    _trade_sessions,
    _trade_codes,
    _trade_history,
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


@pytest.fixture(autouse=True)
def _clean_trade_state():
    """Clear trade state between tests."""
    _trade_sessions.clear()
    _trade_codes.clear()
    _trade_history.clear()
    yield
    _trade_sessions.clear()
    _trade_codes.clear()
    _trade_history.clear()


def _create_game_with_team(name: str, team_size: int = 3) -> str:
    """Helper: create a game and add extra Pokemon to the team."""
    game = create_game(name, 1)  # Bulbasaur starter
    game_id = game["id"]
    # Add extra Pokemon to ensure we have enough for trading
    for i in range(team_size - 1):
        game["player"]["team"].append({
            "id": 4 + i,
            "name": f"ExtraMon{i}",
            "types": ["fire"],
            "stats": {"hp": 100, "attack": 100, "defense": 100, "sp_attack": 100, "sp_defense": 100, "speed": 100},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "test.png",
            "level": 10,
        })
    return game_id


# ============================================================
# Trade Session Creation
# ============================================================

class TestCreateTradeSession:
    def test_create_session(self):
        gid = _create_game_with_team("Alice")
        session = create_trade_session(gid)
        assert isinstance(session, TradeSession)
        assert session.player1_id == gid
        assert session.player2_id is None
        assert session.status == "waiting"
        assert len(session.trade_code) == 6

    def test_create_session_invalid_game(self):
        with pytest.raises(ValueError, match="Game not found"):
            create_trade_session("nonexistent")

    def test_session_stored_and_retrievable(self):
        gid = _create_game_with_team("Alice")
        session = create_trade_session(gid)
        retrieved = get_trade_session(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id


# ============================================================
# Joining Trade Sessions
# ============================================================

class TestJoinTradeSession:
    def test_join_session(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        joined = join_trade_session(session.trade_code, gid2)
        assert joined.player2_id == gid2
        assert joined.status == "selecting"

    def test_join_invalid_code(self):
        gid = _create_game_with_team("Bob")
        with pytest.raises(ValueError, match="Invalid trade code"):
            join_trade_session("XXXXXX", gid)

    def test_join_own_session(self):
        gid = _create_game_with_team("Alice")
        session = create_trade_session(gid)
        with pytest.raises(ValueError, match="Cannot join your own"):
            join_trade_session(session.trade_code, gid)

    def test_join_full_session(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        gid3 = _create_game_with_team("Charlie")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="full"):
            join_trade_session(session.trade_code, gid3)

    def test_join_invalid_game(self):
        gid1 = _create_game_with_team("Alice")
        session = create_trade_session(gid1)
        with pytest.raises(ValueError, match="Game not found"):
            join_trade_session(session.trade_code, "nonexistent")


# ============================================================
# Trade Offers
# ============================================================

class TestTradeOffers:
    def test_set_offer(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        updated = set_trade_offer(session.id, gid1, 0)
        assert updated.player1_offer is not None
        assert updated.player1_offer.pokemon_index == 0

    def test_set_offer_invalid_index(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="Invalid Pokemon index"):
            set_trade_offer(session.id, gid1, 99)

    def test_cannot_trade_only_pokemon(self):
        gid1 = _create_game_with_team("Alice", team_size=1)
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="only Pokemon"):
            set_trade_offer(session.id, gid1, 0)

    def test_offer_resets_confirmation(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        # Change offer should reset confirmation
        updated = set_trade_offer(session.id, gid1, 1)
        assert updated.player1_confirmed is False

    def test_offer_non_participant(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        gid3 = _create_game_with_team("Charlie")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="not in this trade"):
            set_trade_offer(session.id, gid3, 0)


# ============================================================
# Trade Confirmation & Execution
# ============================================================

class TestTradeExecution:
    def test_single_confirm_waits(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        result = confirm_trade(session.id, gid1)
        assert isinstance(result, TradeSession)
        assert result.status == "confirmed"

    def test_both_confirm_executes(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        result = confirm_trade(session.id, gid2)
        assert isinstance(result, TradeResult)
        assert result.success is True

    def test_trade_swaps_pokemon(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        team1_before = [p["name"] for p in get_player_team(gid1)]
        team2_before = [p["name"] for p in get_player_team(gid2)]

        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)  # Offer first Pokemon
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        confirm_trade(session.id, gid2)

        team1_after = [p["name"] for p in get_player_team(gid1)]
        team2_after = [p["name"] for p in get_player_team(gid2)]

        # Player 1 should have player 2's first Pokemon
        assert team2_before[0] in team1_after
        # Player 2 should have player 1's first Pokemon
        assert team1_before[0] in team2_after

    def test_traded_pokemon_has_metadata(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")

        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        result = confirm_trade(session.id, gid2)

        assert result.player1_given["is_outsider"] is True
        assert result.player1_given["original_trainer"] == "Alice"
        assert result.player1_given["traded_date"] is not None
        assert result.player2_given["original_trainer"] == "Bob"

    def test_confirm_without_offer_fails(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        with pytest.raises(ValueError, match="No offer set"):
            confirm_trade(session.id, gid1)

    def test_session_cleaned_up_after_trade(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        confirm_trade(session.id, gid2)
        assert get_trade_session(session.id) is None


# ============================================================
# Cancel Operations
# ============================================================

class TestCancelOperations:
    def test_cancel_offer(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        updated = cancel_offer(session.id, gid1)
        assert updated.player1_offer is None
        assert updated.status == "selecting"

    def test_cancel_session(self):
        gid1 = _create_game_with_team("Alice")
        session = create_trade_session(gid1)
        assert cancel_trade_session(session.id) is True
        assert get_trade_session(session.id) is None

    def test_cancel_nonexistent_session(self):
        assert cancel_trade_session("nonexistent") is False


# ============================================================
# Trade History
# ============================================================

class TestTradeHistory:
    def test_history_recorded(self):
        gid1 = _create_game_with_team("Alice")
        gid2 = _create_game_with_team("Bob")
        session = create_trade_session(gid1)
        join_trade_session(session.trade_code, gid2)
        set_trade_offer(session.id, gid1, 0)
        set_trade_offer(session.id, gid2, 0)
        confirm_trade(session.id, gid1)
        confirm_trade(session.id, gid2)

        history1 = get_trade_history(gid1)
        history2 = get_trade_history(gid2)
        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0].partner_name == "Bob"
        assert history2[0].partner_name == "Alice"

    def test_empty_history(self):
        assert get_trade_history("nobody") == []


# ============================================================
# Helper
# ============================================================

class TestHelpers:
    def test_get_player_team(self):
        gid = _create_game_with_team("Alice")
        team = get_player_team(gid)
        assert team is not None
        assert len(team) == 3

    def test_get_player_team_invalid(self):
        assert get_player_team("nonexistent") is None
