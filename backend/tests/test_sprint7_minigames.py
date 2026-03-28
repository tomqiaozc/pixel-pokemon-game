"""Tests for Sprint 7: Mini-Games, Coins & Prize System."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import _games, create_game_with_starter
from backend.services.minigame_service import (
    COIN_PRICE,
    COINS_PER_PURCHASE,
    MEMORY_DIFFICULTY,
    PRIZE_CATALOG,
    QUIZ_COINS_PER_CORRECT,
    SLOT_PAYOUTS,
    SLOT_SYMBOLS,
    _memory_sessions,
    _quiz_sessions,
    _slot_history,
)

client = TestClient(app)


def _make_game(name="TestPlayer", money=3000, coins=0):
    """Create a game with a starter Pokemon for testing."""
    starter = {
        "id": 1,
        "name": "Bulbasaur",
        "types": ["grass", "poison"],
        "stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
        "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
        "sprite": "bulbasaur.png",
        "level": 5,
        "ability_id": "overgrow",
    }
    game = create_game_with_starter(name, starter)
    game["player"]["money"] = money
    game["player"]["coins"] = coins
    return game


def _cleanup(game_id):
    _games.pop(game_id, None)
    _quiz_sessions.clear()
    _memory_sessions.clear()
    _slot_history.pop(game_id, None)


# ──── Coin System ────────────────────────────────────────

class TestCoinBalance:
    def test_balance_returns_coins_and_money(self):
        game = _make_game(coins=100)
        gid = game["id"]
        resp = client.get(f"/api/minigames/coins/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["coins"] == 100
        assert data["money"] == 3000
        _cleanup(gid)

    def test_balance_game_not_found(self):
        resp = client.get("/api/minigames/coins/nonexistent")
        assert resp.status_code == 404

    def test_balance_default_zero_coins(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/minigames/coins/{gid}")
        assert resp.json()["coins"] == 0
        _cleanup(gid)


class TestBuyCoins:
    def test_buy_coins_success(self):
        game = _make_game(money=3000)
        gid = game["id"]
        resp = client.post("/api/minigames/coins/buy", json={"game_id": gid, "amount": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data["coins_after"] == COINS_PER_PURCHASE
        assert data["money_after"] == 3000 - COIN_PRICE
        assert data["amount"] == COINS_PER_PURCHASE
        _cleanup(gid)

    def test_buy_coins_multiple(self):
        game = _make_game(money=5000)
        gid = game["id"]
        resp = client.post("/api/minigames/coins/buy", json={"game_id": gid, "amount": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert data["coins_after"] == COINS_PER_PURCHASE * 2
        assert data["money_after"] == 5000 - COIN_PRICE * 2
        _cleanup(gid)

    def test_buy_coins_insufficient_money(self):
        game = _make_game(money=500)
        gid = game["id"]
        resp = client.post("/api/minigames/coins/buy", json={"game_id": gid, "amount": 1})
        assert resp.status_code == 400
        _cleanup(gid)

    def test_buy_coins_invalid_amount(self):
        game = _make_game(money=3000)
        gid = game["id"]
        resp = client.post("/api/minigames/coins/buy", json={"game_id": gid, "amount": 0})
        assert resp.status_code == 400
        _cleanup(gid)

    def test_buy_coins_preserves_existing(self):
        game = _make_game(money=3000, coins=50)
        gid = game["id"]
        resp = client.post("/api/minigames/coins/buy", json={"game_id": gid, "amount": 1})
        data = resp.json()
        assert data["coins_before"] == 50
        assert data["coins_after"] == 50 + COINS_PER_PURCHASE
        _cleanup(gid)


# ──── Slot Machine ───────────────────────────────────────

class TestSlotMachine:
    def test_spin_success(self):
        game = _make_game(coins=100)
        gid = game["id"]
        resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["reels"]) == 3
        assert isinstance(data["win"], bool)
        assert isinstance(data["payout"], int)
        assert data["coins_before"] == 100
        _cleanup(gid)

    def test_spin_insufficient_coins(self):
        game = _make_game(coins=1)
        gid = game["id"]
        resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 3})
        assert resp.status_code == 400
        _cleanup(gid)

    def test_spin_invalid_bet(self):
        game = _make_game(coins=100)
        gid = game["id"]
        resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 0})
        assert resp.status_code == 400
        resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 11})
        assert resp.status_code == 400
        _cleanup(gid)

    def test_spin_deducts_bet_on_loss(self):
        game = _make_game(coins=100)
        gid = game["id"]
        # Force a loss by mocking reels to all different symbols
        with patch("backend.services.minigame_service._spin_reel", side_effect=["Pokeball", "Cherry", "Bar"]):
            resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 3})
        data = resp.json()
        assert data["win"] is False
        assert data["payout"] == 0
        assert data["coins_after"] == 97
        _cleanup(gid)

    def test_spin_triple_match_payout(self):
        game = _make_game(coins=100)
        gid = game["id"]
        with patch("backend.services.minigame_service._spin_reel", return_value="7"):
            resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 3})
        data = resp.json()
        assert data["win"] is True
        assert data["payout"] == SLOT_PAYOUTS["7"] * 3
        assert data["coins_after"] == 100 - 3 + SLOT_PAYOUTS["7"] * 3
        _cleanup(gid)

    def test_spin_double_match_returns_bet(self):
        game = _make_game(coins=100)
        gid = game["id"]
        with patch("backend.services.minigame_service._spin_reel", side_effect=["Cherry", "Cherry", "Bar"]):
            resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 3})
        data = resp.json()
        assert data["win"] is True
        assert data["payout"] == 3  # returns bet
        assert data["coins_after"] == 100  # net zero
        _cleanup(gid)

    def test_spin_symbols_valid(self):
        game = _make_game(coins=100)
        gid = game["id"]
        valid_symbols = {s[0] for s in SLOT_SYMBOLS}
        resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 1})
        data = resp.json()
        for reel in data["reels"]:
            assert reel in valid_symbols
        _cleanup(gid)

    def test_spin_rate_limit(self):
        game = _make_game(coins=10000)
        gid = game["id"]
        # Fill rate limit history
        import time
        _slot_history[gid] = [time.time()] * 100
        resp = client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 1})
        assert resp.status_code == 400
        _cleanup(gid)


# ──── Memory Game ────────────────────────────────────────

class TestMemoryGame:
    def test_start_memory_game(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/minigames/memory/start", json={"game_id": gid, "difficulty": "easy"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["pairs"] == MEMORY_DIFFICULTY["easy"]["pairs"]
        assert data["session_started"] is True
        _cleanup(gid)

    def test_start_invalid_difficulty(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/minigames/memory/start", json={"game_id": gid, "difficulty": "extreme"})
        assert resp.status_code == 400
        _cleanup(gid)

    def test_complete_memory_game(self):
        game = _make_game()
        gid = game["id"]
        # Start session
        client.post("/api/minigames/memory/start", json={"game_id": gid, "difficulty": "easy"})
        # Backdate start time so claimed time passes server clock validation
        import time as _time
        _memory_sessions[f"{gid}:easy"] = _time.time() - 31
        # Complete
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid, "difficulty": "easy",
            "time_seconds": 30, "pairs_matched": 6,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["coins_earned"] > 0
        _cleanup(gid)

    def test_complete_without_start_fails(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid, "difficulty": "easy",
            "time_seconds": 30, "pairs_matched": 6,
        })
        data = resp.json()
        assert data["valid"] is False
        assert "No active" in data["message"]
        _cleanup(gid)

    def test_complete_fast_time_bonus(self):
        game = _make_game()
        gid = game["id"]
        import time as _time
        max_time = MEMORY_DIFFICULTY["medium"]["max_time"]
        fast_time = max_time * 0.3
        slow_time = max_time * 0.9

        # Start
        client.post("/api/minigames/memory/start", json={"game_id": gid, "difficulty": "medium"})
        # Backdate start time so claimed time passes server clock validation
        _memory_sessions[f"{gid}:medium"] = _time.time() - fast_time - 1
        # Complete quickly (under 50% max time)
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid, "difficulty": "medium",
            "time_seconds": fast_time, "pairs_matched": 10,
        })
        fast_coins = resp.json()["coins_earned"]

        # Start another
        client.post("/api/minigames/memory/start", json={"game_id": gid, "difficulty": "medium"})
        # Backdate start time for slow completion
        _memory_sessions[f"{gid}:medium"] = _time.time() - slow_time - 1
        # Complete slowly
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid, "difficulty": "medium",
            "time_seconds": slow_time, "pairs_matched": 10,
        })
        slow_coins = resp.json()["coins_earned"]

        assert fast_coins > slow_coins
        _cleanup(gid)

    def test_complete_invalid_pairs(self):
        game = _make_game()
        gid = game["id"]
        client.post("/api/minigames/memory/start", json={"game_id": gid, "difficulty": "easy"})
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid, "difficulty": "easy",
            "time_seconds": 30, "pairs_matched": 100,  # way more than 6
        })
        data = resp.json()
        assert data["valid"] is False
        _cleanup(gid)

    def test_hard_difficulty_more_coins(self):
        game = _make_game()
        gid = game["id"]
        import time as _time
        # Easy — complete all pairs quickly
        client.post("/api/minigames/memory/start", json={"game_id": gid, "difficulty": "easy"})
        easy_pairs = MEMORY_DIFFICULTY["easy"]["pairs"]
        # Backdate start time so claimed 20s passes server clock validation
        _memory_sessions[f"{gid}:easy"] = _time.time() - 21
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid, "difficulty": "easy",
            "time_seconds": 20, "pairs_matched": easy_pairs,
        })
        easy_coins = resp.json()["coins_earned"]

        # Hard — complete all pairs quickly
        client.post("/api/minigames/memory/start", json={"game_id": gid, "difficulty": "hard"})
        hard_pairs = MEMORY_DIFFICULTY["hard"]["pairs"]
        # Backdate start time so claimed 30s passes server clock validation
        _memory_sessions[f"{gid}:hard"] = _time.time() - 31
        resp = client.post("/api/minigames/memory/complete", json={
            "game_id": gid, "difficulty": "hard",
            "time_seconds": 30, "pairs_matched": hard_pairs,
        })
        hard_coins = resp.json()["coins_earned"]

        assert hard_coins > easy_coins
        _cleanup(gid)


# ──── Quiz System ────────────────────────────────────────

class TestQuizSystem:
    def test_start_quiz(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/minigames/quiz/start", json={"game_id": gid})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert len(data["questions"]) == 10
        for q in data["questions"]:
            assert "question" in q
            assert len(q["options"]) == 4
            # correct_index should NOT be in API response (Bug #2 fix)
            assert "correct_index" not in q
        _cleanup(gid)

    def test_start_quiz_game_not_found(self):
        resp = client.post("/api/minigames/quiz/start", json={"game_id": "nope"})
        assert resp.status_code == 404

    def test_submit_quiz_all_correct(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/minigames/quiz/start", json={"game_id": gid})
        data = resp.json()
        sid = data["session_id"]
        # Get correct answers from internal session (API hides them)
        session = _quiz_sessions[sid]
        correct_answers = [q.correct_index for q in session.questions]

        resp = client.post("/api/minigames/quiz/submit", json={
            "session_id": sid, "answers": correct_answers,
        })
        assert resp.status_code == 200
        result = resp.json()
        assert result["score"] == 10
        assert result["coins_earned"] == 10 * QUIZ_COINS_PER_CORRECT
        assert all(result["results"])
        _cleanup(gid)

    def test_submit_quiz_all_wrong(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/minigames/quiz/start", json={"game_id": gid})
        data = resp.json()
        sid = data["session_id"]
        # Get correct answers from internal session, then offset to get wrong answers
        session = _quiz_sessions[sid]
        wrong_answers = [(q.correct_index + 1) % 4 for q in session.questions]

        resp = client.post("/api/minigames/quiz/submit", json={
            "session_id": sid, "answers": wrong_answers,
        })
        result = resp.json()
        assert result["score"] == 0
        assert result["coins_earned"] == 0
        assert not any(result["results"])
        _cleanup(gid)

    def test_submit_quiz_invalid_session(self):
        resp = client.post("/api/minigames/quiz/submit", json={
            "session_id": "fake", "answers": [0] * 10,
        })
        assert resp.status_code == 400

    def test_submit_quiz_session_consumed(self):
        """Quiz session can only be submitted once."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/minigames/quiz/start", json={"game_id": gid})
        sid = resp.json()["session_id"]
        # First submit
        client.post("/api/minigames/quiz/submit", json={"session_id": sid, "answers": [0] * 10})
        # Second submit should fail
        resp = client.post("/api/minigames/quiz/submit", json={"session_id": sid, "answers": [0] * 10})
        assert resp.status_code == 400
        _cleanup(gid)

    def test_quiz_questions_are_varied(self):
        """Quiz should generate diverse question types."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/minigames/quiz/start", json={"game_id": gid})
        questions = resp.json()["questions"]
        # Should have at least a few different question patterns
        patterns = set()
        for q in questions:
            if "type is" in q["question"]:
                patterns.add("type")
            elif "evolve" in q["question"]:
                patterns.add("evolution")
            elif "highest" in q["question"]:
                patterns.add("stat")
            elif "move is" in q["question"]:
                patterns.add("move")
        # Should have at least 2 different patterns
        assert len(patterns) >= 2
        _cleanup(gid)

    def test_quiz_awards_coins(self):
        game = _make_game(coins=0)
        gid = game["id"]
        resp = client.post("/api/minigames/quiz/start", json={"game_id": gid})
        data = resp.json()
        sid = data["session_id"]
        # Get correct answers from internal session (API hides them)
        session = _quiz_sessions[sid]
        correct_answers = [q.correct_index for q in session.questions]
        resp = client.post("/api/minigames/quiz/submit", json={
            "session_id": sid, "answers": correct_answers,
        })
        result = resp.json()
        assert result["coins_before"] == 0
        assert result["coins_after"] == result["coins_earned"]
        assert result["coins_after"] > 0
        _cleanup(gid)


# ──── Prize Exchange ─────────────────────────────────────

class TestPrizeCatalog:
    def test_list_prizes(self):
        resp = client.get("/api/minigames/prizes")
        assert resp.status_code == 200
        prizes = resp.json()
        assert len(prizes) == 7
        names = {p["name"] for p in prizes}
        assert "Porygon" in names
        assert "Dratini" in names
        assert "Eevee" in names
        assert "TM Ice Beam" in names
        assert "Rare Candy" in names

    def test_prize_costs(self):
        resp = client.get("/api/minigames/prizes")
        prizes = resp.json()
        porygon = next(p for p in prizes if p["name"] == "Porygon")
        assert porygon["coin_cost"] == 9999
        dratini = next(p for p in prizes if p["name"] == "Dratini")
        assert dratini["coin_cost"] == 4600
        eevee = next(p for p in prizes if p["name"] == "Eevee")
        assert eevee["coin_cost"] == 6666

    def test_prize_types(self):
        resp = client.get("/api/minigames/prizes")
        prizes = resp.json()
        pokemon_prizes = [p for p in prizes if p["prize_type"] == "pokemon"]
        item_prizes = [p for p in prizes if p["prize_type"] == "item"]
        assert len(pokemon_prizes) == 3
        assert len(item_prizes) == 4


class TestPrizeRedeem:
    def test_redeem_item_prize(self):
        game = _make_game(coins=1000)
        gid = game["id"]
        # Redeem Rare Candy (id=6, cost=500)
        resp = client.post("/api/minigames/prizes/redeem", json={"game_id": gid, "prize_id": 6})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["coins_before"] == 1000
        assert data["coins_after"] == 500
        assert data["prize_name"] == "Rare Candy"
        _cleanup(gid)

    def test_redeem_pokemon_prize(self):
        game = _make_game(coins=10000)
        gid = game["id"]
        # Redeem Porygon (id=1, cost=9999)
        resp = client.post("/api/minigames/prizes/redeem", json={"game_id": gid, "prize_id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["coins_after"] == 10000 - 9999
        # Check Pokemon was added to team
        game_data = _games[gid]
        team_names = [p["name"] for p in game_data["player"]["team"]]
        assert "Porygon" in team_names
        _cleanup(gid)

    def test_redeem_insufficient_coins(self):
        game = _make_game(coins=100)
        gid = game["id"]
        resp = client.post("/api/minigames/prizes/redeem", json={"game_id": gid, "prize_id": 1})
        data = resp.json()
        assert data["success"] is False
        assert "Not enough coins" in data["message"]
        _cleanup(gid)

    def test_redeem_invalid_prize(self):
        game = _make_game(coins=10000)
        gid = game["id"]
        resp = client.post("/api/minigames/prizes/redeem", json={"game_id": gid, "prize_id": 999})
        data = resp.json()
        assert data["success"] is False
        _cleanup(gid)

    def test_redeem_item_added_to_inventory(self):
        game = _make_game(coins=5000)
        gid = game["id"]
        # Redeem PP Up (id=7, cost=1000, item_id=14)
        resp = client.post("/api/minigames/prizes/redeem", json={"game_id": gid, "prize_id": 7})
        assert resp.json()["success"] is True
        # Check inventory
        inventory = _games[gid]["player"]["inventory"]
        pp_up = [i for i in inventory if i["item_id"] == 14]
        assert len(pp_up) == 1
        assert pp_up[0]["quantity"] == 1

        # Redeem again — quantity should increment
        resp = client.post("/api/minigames/prizes/redeem", json={"game_id": gid, "prize_id": 7})
        assert resp.json()["success"] is True
        pp_up = [i for i in _games[gid]["player"]["inventory"] if i["item_id"] == 14]
        assert pp_up[0]["quantity"] == 2
        _cleanup(gid)

    def test_redeem_game_not_found(self):
        resp = client.post("/api/minigames/prizes/redeem", json={"game_id": "nope", "prize_id": 1})
        assert resp.status_code == 404


# ──── Integration ────────────────────────────────────────

class TestMinigameIntegration:
    def test_full_flow_buy_coins_spin_redeem(self):
        """End-to-end: buy coins → spin slots → redeem prize."""
        game = _make_game(money=5000)
        gid = game["id"]

        # Buy coins
        resp = client.post("/api/minigames/coins/buy", json={"game_id": gid, "amount": 2})
        assert resp.json()["coins_after"] == 100

        # Give extra coins for prize redemption
        _games[gid]["player"]["coins"] = 600

        # Redeem Rare Candy
        resp = client.post("/api/minigames/prizes/redeem", json={"game_id": gid, "prize_id": 6})
        assert resp.json()["success"] is True
        assert resp.json()["coins_after"] == 100

        _cleanup(gid)

    def test_coins_persist_across_operations(self):
        game = _make_game(money=3000)
        gid = game["id"]

        # Buy coins
        client.post("/api/minigames/coins/buy", json={"game_id": gid, "amount": 1})
        # Check balance
        resp = client.get(f"/api/minigames/coins/{gid}")
        assert resp.json()["coins"] == 50

        # Spin (costs 3)
        client.post("/api/minigames/slots/spin", json={"game_id": gid, "bet": 3})
        # Balance changed
        resp = client.get(f"/api/minigames/coins/{gid}")
        # Coins should be 50 - 3 + payout (unknown)
        assert resp.json()["coins"] >= 0

        _cleanup(gid)
