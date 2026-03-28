"""Tests for Sprint 7 QA-B mini-game backend bug fixes."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import _games, create_game
from backend.services.minigame_service import (
    MEMORY_DIFFICULTY,
    _quiz_sessions,
    _memory_sessions,
    _slot_history,
    buy_coins,
    start_quiz,
    spin_slots,
    redeem_prize,
)
from backend.services.pokedex_service import _pc_boxes

client = TestClient(app)


def _make_game(name: str = "TestPlayer", money: int = 10000, coins: int = 0) -> str:
    game = create_game(name, 1)
    gid = game["id"]
    game["player"]["money"] = money
    game["player"]["coins"] = coins
    return gid


def _cleanup(gid: str):
    _games.pop(gid, None)
    _quiz_sessions.clear()
    _memory_sessions.clear()
    _slot_history.pop(gid, None)
    _pc_boxes.pop(gid, None)


# ============================================================
# Bug #1: BuyCoins field mismatch
# Frontend sends money_amount (dollar amount), backend expects amount (purchase count)
# ============================================================

class TestBuyCoinsFieldMismatch:
    def test_buy_coins_api_accepts_money_amount_field(self):
        """Frontend sends money_amount=1000 meaning $1000. Backend should accept this."""
        gid = _make_game(money=5000)
        resp = client.post("/api/minigames/coins/buy", json={
            "game_id": gid,
            "money_amount": 1000,
        })
        assert resp.status_code == 200
        data = resp.json()
        # $1000 = 50 coins
        assert data["coins_after"] == 50
        assert data["money_after"] == 4000
        _cleanup(gid)

    def test_buy_coins_api_money_amount_2000(self):
        """$2000 should yield 100 coins."""
        gid = _make_game(money=5000)
        resp = client.post("/api/minigames/coins/buy", json={
            "game_id": gid,
            "money_amount": 2000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["coins_after"] == 100
        assert data["money_after"] == 3000
        _cleanup(gid)

    def test_buy_coins_api_money_amount_5000(self):
        """$5000 should yield 250 coins."""
        gid = _make_game(money=10000)
        resp = client.post("/api/minigames/coins/buy", json={
            "game_id": gid,
            "money_amount": 5000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["coins_after"] == 250
        assert data["money_after"] == 5000
        _cleanup(gid)

    def test_buy_coins_api_money_amount_insufficient(self):
        """Should fail if not enough money."""
        gid = _make_game(money=500)
        resp = client.post("/api/minigames/coins/buy", json={
            "game_id": gid,
            "money_amount": 1000,
        })
        assert resp.status_code == 400
        _cleanup(gid)


# ============================================================
# Bug #2: Quiz correct_index exposed to client
# ============================================================

class TestQuizCorrectIndexHidden:
    def test_quiz_start_hides_correct_index(self):
        """API response should NOT include correct_index in questions."""
        gid = _make_game()
        resp = client.post("/api/minigames/quiz/start", json={"game_id": gid})
        assert resp.status_code == 200
        data = resp.json()
        for q in data["questions"]:
            assert "correct_index" not in q, \
                f"correct_index leaked in question: {q['question']}"
        _cleanup(gid)

    def test_quiz_session_still_stores_correct_index(self):
        """Internal QuizSession should still have correct_index for grading."""
        gid = _make_game()
        session = start_quiz(gid)
        assert session is not None
        for q in session.questions:
            assert q.correct_index is not None
            assert 0 <= q.correct_index < len(q.options)
        _cleanup(gid)


# ============================================================
# Bug #3: Memory pair counts mismatch
# Backend should use 8/10/12 to match frontend grids (4x4/5x4/6x4)
# ============================================================

class TestMemoryPairCounts:
    def test_easy_pairs_is_8(self):
        assert MEMORY_DIFFICULTY["easy"]["pairs"] == 8

    def test_medium_pairs_is_10(self):
        assert MEMORY_DIFFICULTY["medium"]["pairs"] == 10

    def test_hard_pairs_is_12(self):
        assert MEMORY_DIFFICULTY["hard"]["pairs"] == 12

    def test_memory_start_returns_correct_pairs(self):
        gid = _make_game()
        resp = client.post("/api/minigames/memory/start", json={
            "game_id": gid,
            "difficulty": "easy",
        })
        assert resp.status_code == 200
        assert resp.json()["pairs"] == 8
        _cleanup(gid)


# ============================================================
# Bug #4: Memory time limits diverge
# Backend should use 65/80/95 (slightly above frontend 60/75/90 for network lag)
# ============================================================

class TestMemoryTimeLimits:
    def test_easy_max_time_is_65(self):
        assert MEMORY_DIFFICULTY["easy"]["max_time"] == 65

    def test_medium_max_time_is_80(self):
        assert MEMORY_DIFFICULTY["medium"]["max_time"] == 80

    def test_hard_max_time_is_95(self):
        assert MEMORY_DIFFICULTY["hard"]["max_time"] == 95


# ============================================================
# Bug #5: Prize Pokemon lost when team full — no PC fallback
# ============================================================

class TestPrizePokemonPCFallback:
    def test_prize_pokemon_goes_to_pc_when_team_full(self):
        """When team has 6 Pokemon, prize Pokemon should go to PC storage."""
        gid = _make_game(coins=10000)
        game = _games[gid]
        # Fill team to 6
        while len(game["player"]["team"]) < 6:
            game["player"]["team"].append({
                "id": 4, "name": "Filler", "types": ["normal"],
                "stats": {"hp": 100, "attack": 100, "defense": 100,
                          "sp_attack": 100, "sp_defense": 100, "speed": 100},
                "moves": [{"name": "Tackle", "type": "normal", "power": 40,
                          "accuracy": 100, "pp": 35}],
                "sprite": "filler.png", "level": 10,
            })
        assert len(game["player"]["team"]) == 6

        # Redeem Dratini (prize_id=2, cost=4600 coins)
        resp = client.post("/api/minigames/prizes/redeem", json={
            "game_id": gid,
            "prize_id": 2,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        # Team should still be 6
        assert len(game["player"]["team"]) == 6

        # Pokemon should be in PC
        from backend.services.pokedex_service import get_pc_boxes
        boxes = get_pc_boxes(gid)
        pc_pokemon = []
        for box in boxes:
            pc_pokemon.extend(box.pokemon)
        assert len(pc_pokemon) == 1
        assert pc_pokemon[0]["name"] == "Dratini"
        _cleanup(gid)

    def test_prize_pokemon_goes_to_team_when_not_full(self):
        """Normal case: team not full, Pokemon added to team."""
        gid = _make_game(coins=10000)
        game = _games[gid]
        team_size_before = len(game["player"]["team"])

        resp = client.post("/api/minigames/prizes/redeem", json={
            "game_id": gid,
            "prize_id": 2,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert len(game["player"]["team"]) == team_size_before + 1
        _cleanup(gid)


# ============================================================
# Bug #7: Slot bet default mismatch
# Backend defaults bet=3, should be bet=1 to match frontend
# ============================================================

class TestSlotBetDefault:
    def test_slot_default_bet_is_1(self):
        """Spinning without specifying bet should use 1 coin, not 3."""
        gid = _make_game(coins=2)  # Only 2 coins — bet=3 would fail, bet=1 should work
        resp = client.post("/api/minigames/slots/spin", json={
            "game_id": gid,
        })
        assert resp.status_code == 200
        data = resp.json()
        # With only 2 coins and default bet=1, spin should succeed
        # coins_before should be 2
        assert data["coins_before"] == 2
        _cleanup(gid)

    def test_slot_explicit_bet_still_works(self):
        """Explicit bet value should still be respected."""
        gid = _make_game(coins=10)
        resp = client.post("/api/minigames/slots/spin", json={
            "game_id": gid,
            "bet": 5,
        })
        assert resp.status_code == 200
        assert resp.json()["coins_before"] == 10
        _cleanup(gid)


# ============================================================
# MG-H02: Memory time not validated against server clock
# Prevent instant completions by checking claimed time vs actual elapsed
# ============================================================

class TestMemoryServerTimeValidation:
    def test_instant_completion_rejected(self):
        """Claiming 30s completion when only 1s actually elapsed should be rejected."""
        import time as _time
        gid = _make_game()
        # Start memory game
        client.post("/api/minigames/memory/start", json={
            "game_id": gid,
            "difficulty": "easy",
        })
        # Immediately complete claiming 30 seconds elapsed (impossible)
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid,
            "difficulty": "easy",
            "time_seconds": 30,
            "pairs_matched": 8,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert "time" in data["message"].lower()
        _cleanup(gid)

    def test_honest_completion_accepted(self):
        """Claiming ~2s when 2s actually elapsed should be accepted."""
        import time as _time
        gid = _make_game()
        client.post("/api/minigames/memory/start", json={
            "game_id": gid,
            "difficulty": "easy",
        })
        # Wait a real 2 seconds
        _time.sleep(2)
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid,
            "difficulty": "easy",
            "time_seconds": 2,
            "pairs_matched": 4,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        _cleanup(gid)

    def test_slightly_inflated_time_rejected(self):
        """Claiming 20s when only 1s elapsed — still fake."""
        gid = _make_game()
        client.post("/api/minigames/memory/start", json={
            "game_id": gid,
            "difficulty": "medium",
        })
        # Immediately complete claiming 20s (>2s tolerance over actual ~0s)
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid,
            "difficulty": "medium",
            "time_seconds": 20,
            "pairs_matched": 10,
        })
        data = resp.json()
        assert data["valid"] is False
        _cleanup(gid)
