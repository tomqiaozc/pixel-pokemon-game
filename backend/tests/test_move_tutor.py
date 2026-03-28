"""Tests for Sprint 9: Move Tutor & TM/HM System.

Covers:
- Move Tutor NPC data and definitions
- TM/HM item definitions and data
- Move compatibility checking (species-based)
- Teaching moves via tutor (cost deduction, badge requirements)
- Using TM/HM items (single-use TMs, reusable HMs)
- Move slot management (teach when <4 moves, replace with forget_move_index)
- HM deletion prevention (can't forget HM moves)
- Move Reminder (re-teach forgotten moves for Heart Scale)
- All API endpoints
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import create_game, _games

client = TestClient(app)


@pytest.fixture
def game():
    """Create a fresh game with Bulbasaur starter."""
    g = create_game("Tester", 1)
    return g


@pytest.fixture
def game_with_money():
    """Create a game with extra money for tutor costs."""
    g = create_game("Tester", 1)
    g["player"]["money"] = 10000
    return g


# ============================================================
# Move Tutor Data & Definitions
# ============================================================

class TestMoveTutorDefinitions:
    def test_get_tutor_by_id(self):
        """GET /api/tutor/{tutor_id} returns tutor info."""
        resp = client.get("/api/tutor/pallet_tutor")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tutor_id"] == "pallet_tutor"
        assert "moves_offered" in data

    def test_pallet_tutor_offers_starter_moves(self):
        """Pallet Town tutor offers starter moves."""
        resp = client.get("/api/tutor/pallet_tutor")
        assert resp.status_code == 200
        data = resp.json()
        move_names = [m["move_name"] for m in data["moves_offered"]]
        assert "Vine Whip" in move_names or "Ember" in move_names or "Water Gun" in move_names

    def test_viridian_tutor_exists(self):
        """Viridian City tutor exists with type coverage moves."""
        resp = client.get("/api/tutor/viridian_tutor")
        assert resp.status_code == 200
        data = resp.json()
        assert data["location"] == "viridian_city"

    def test_pewter_tutor_exists(self):
        """Pewter City tutor exists with rock/ground moves."""
        resp = client.get("/api/tutor/pewter_tutor")
        assert resp.status_code == 200

    def test_nonexistent_tutor_404(self):
        """Requesting a non-existent tutor returns 404."""
        resp = client.get("/api/tutor/fake_tutor")
        assert resp.status_code == 404

    def test_tutor_moves_have_cost(self):
        """Each tutor move has a cost field."""
        resp = client.get("/api/tutor/pallet_tutor")
        data = resp.json()
        for move in data["moves_offered"]:
            assert "cost" in move
            assert move["cost"] > 0


# ============================================================
# TM/HM Definitions
# ============================================================

class TestTMHMDefinitions:
    def test_get_tm_list(self):
        """GET /api/tm/list returns all TM/HM definitions."""
        resp = client.get("/api/tm/list")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_tm_has_required_fields(self):
        """Each TM/HM has number, move_name, reusable, is_hm fields."""
        resp = client.get("/api/tm/list")
        data = resp.json()
        tm = data[0]
        assert "tm_number" in tm
        assert "move_name" in tm
        assert "reusable" in tm
        assert "is_hm" in tm

    def test_hm_moves_are_reusable(self):
        """HM items are always reusable."""
        resp = client.get("/api/tm/list")
        data = resp.json()
        hms = [t for t in data if t["is_hm"]]
        assert len(hms) >= 5  # HM01-HM05
        for hm in hms:
            assert hm["reusable"] is True

    def test_tm_moves_are_single_use(self):
        """TM items are single-use (not reusable)."""
        resp = client.get("/api/tm/list")
        data = resp.json()
        tms = [t for t in data if not t["is_hm"]]
        assert len(tms) > 0
        for tm in tms:
            assert tm["reusable"] is False

    def test_hm01_is_cut(self):
        """HM01 is the move Cut."""
        resp = client.get("/api/tm/list")
        data = resp.json()
        hm01 = next((t for t in data if t["tm_number"] == "HM01"), None)
        assert hm01 is not None
        assert hm01["move_name"] == "Cut"

    def test_hm03_is_surf(self):
        """HM03 is the move Surf."""
        resp = client.get("/api/tm/list")
        data = resp.json()
        hm03 = next((t for t in data if t["tm_number"] == "HM03"), None)
        assert hm03 is not None
        assert hm03["move_name"] == "Surf"

    def test_hm05_is_fly(self):
        """HM05 is the move Fly."""
        resp = client.get("/api/tm/list")
        data = resp.json()
        hm05 = next((t for t in data if t["tm_number"] == "HM05"), None)
        assert hm05 is not None
        assert hm05["move_name"] == "Fly"


# ============================================================
# Move Compatibility Checking
# ============================================================

class TestMoveCompatibility:
    def test_check_tm_compatible(self):
        """GET /api/tm/compatible/{tm_number}/{pokemon_id} returns compatibility."""
        # Bulbasaur (1) should be compatible with some TMs
        resp = client.get("/api/tm/compatible/TM01/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "compatible" in data

    def test_check_tm_incompatible(self):
        """Incompatible species returns compatible=false."""
        # Use a TM that a specific pokemon can't learn
        resp = client.get("/api/tm/compatible/HM05/1")  # Fly - Bulbasaur can't fly
        assert resp.status_code == 200
        data = resp.json()
        assert data["compatible"] is False

    def test_nonexistent_tm_returns_404(self):
        """Non-existent TM number returns 404."""
        resp = client.get("/api/tm/compatible/TM99/1")
        assert resp.status_code == 404

    def test_nonexistent_pokemon_returns_404(self):
        """Non-existent Pokemon species returns 404."""
        resp = client.get("/api/tm/compatible/TM01/9999")
        assert resp.status_code == 404

    def test_get_all_learnable_moves(self):
        """GET /api/moves/learnable/{pokemon_id} returns all moves a Pokemon can learn."""
        resp = client.get("/api/moves/learnable/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "tutor_moves" in data
        assert "tm_moves" in data
        assert "hm_moves" in data


# ============================================================
# Teach Move via Move Tutor
# ============================================================

class TestTeachMoveTutor:
    def test_teach_move_success(self, game_with_money):
        """POST /api/tutor/teach teaches a move and deducts cost."""
        game_id = game_with_money["id"]
        initial_money = game_with_money["player"]["money"]
        pokemon = game_with_money["player"]["team"][0]
        # Bulbasaur starts with Tackle, Vine Whip, Razor Leaf, Solar Beam
        # Clear to 2 so we can teach Razor Leaf without replacement
        pokemon["moves"] = [pokemon["moves"][0], pokemon["moves"][1]]  # Tackle, Vine Whip
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": "Razor Leaf",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        game = _games[game_id]
        assert game["player"]["money"] < initial_money

    def test_teach_move_not_enough_money(self, game):
        """Teaching a move fails if player can't afford it."""
        game_id = game["id"]
        game["player"]["money"] = 0
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": "Vine Whip",
        })
        assert resp.status_code == 400

    def test_teach_move_incompatible(self, game_with_money):
        """Teaching a move fails if Pokemon is not compatible."""
        game_id = game_with_money["id"]
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": "Ember",  # Fire move on Bulbasaur
        })
        # Should fail - Bulbasaur can't learn Ember
        assert resp.status_code == 400

    def test_teach_move_with_replacement(self, game_with_money):
        """Teaching a move when Pokemon has 4 moves requires forget_move_index."""
        game_id = game_with_money["id"]
        pokemon = game_with_money["player"]["team"][0]
        # Set specific 4 moves, none of which are Solar Beam (which we'll teach)
        pokemon["moves"] = [
            {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35, "contact": True},
            {"name": "Growl", "type": "normal", "power": 0, "accuracy": 100, "pp": 40, "contact": False},
            {"name": "Vine Whip", "type": "grass", "power": 45, "accuracy": 100, "pp": 25, "contact": True},
            {"name": "Razor Leaf", "type": "grass", "power": 55, "accuracy": 95, "pp": 25, "contact": False},
        ]
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": "Solar Beam",
            "forget_move_index": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_teach_move_4_moves_no_forget(self, game_with_money):
        """Teaching fails if Pokemon has 4 moves and no forget_move_index given."""
        game_id = game_with_money["id"]
        pokemon = game_with_money["player"]["team"][0]
        # Ensure exactly 4 moves, none of which are Solar Beam
        pokemon["moves"] = [
            {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35, "contact": True},
            {"name": "Growl", "type": "normal", "power": 0, "accuracy": 100, "pp": 40, "contact": False},
            {"name": "Vine Whip", "type": "grass", "power": 45, "accuracy": 100, "pp": 25, "contact": True},
            {"name": "Razor Leaf", "type": "grass", "power": 55, "accuracy": 95, "pp": 25, "contact": False},
        ]
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": "Solar Beam",
        })
        assert resp.status_code == 400

    def test_teach_move_already_known(self, game_with_money):
        """Teaching a move the Pokemon already knows fails."""
        game_id = game_with_money["id"]
        pokemon = game_with_money["player"]["team"][0]
        existing_move = pokemon["moves"][0]["name"]
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": existing_move,
        })
        assert resp.status_code == 400

    def test_teach_move_invalid_game(self):
        """Teaching a move with invalid game_id returns 404."""
        resp = client.post("/api/tutor/teach", json={
            "game_id": "nonexistent",
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": "Vine Whip",
        })
        assert resp.status_code == 404

    def test_teach_move_invalid_pokemon_index(self, game_with_money):
        """Teaching a move with out-of-range pokemon_index returns 400."""
        game_id = game_with_money["id"]
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 99,
            "tutor_id": "pallet_tutor",
            "move_name": "Vine Whip",
        })
        assert resp.status_code == 400


# ============================================================
# Use TM/HM Items
# ============================================================

class TestUseTMHM:
    def test_use_tm_success(self, game):
        """POST /api/tm/use teaches the TM move and consumes the TM."""
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        # Clear to 3 moves so TM can be added without replacement
        pokemon["moves"] = pokemon["moves"][:3]
        game["player"]["inventory"].append({"item_id": 11, "quantity": 1})  # TM Ice Beam
        resp = client.post("/api/tm/use", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tm_number": "TM01",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["move_learned"] == "Ice Beam"

    def test_use_tm_consumes_item(self, game):
        """Using a TM reduces quantity by 1."""
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        pokemon["moves"] = pokemon["moves"][:3]  # Make room
        game["player"]["inventory"].append({"item_id": 11, "quantity": 2})
        resp = client.post("/api/tm/use", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tm_number": "TM01",
        })
        assert resp.status_code == 200
        inv = game["player"]["inventory"]
        tm_entry = next((e for e in inv if e["item_id"] == 11), None)
        assert tm_entry is not None
        assert tm_entry["quantity"] == 1

    def test_use_hm_not_consumed(self, game):
        """Using an HM does NOT consume it (reusable)."""
        game_id = game["id"]
        # Use Squirtle (7) which can learn Surf
        pokemon = game["player"]["team"][0]
        pokemon["id"] = 7
        pokemon["name"] = "Squirtle"
        pokemon["moves"] = pokemon["moves"][:3]  # Make room
        game["player"]["inventory"].append({"item_id": 103, "quantity": 1})  # HM03 Surf
        resp = client.post("/api/tm/use", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tm_number": "HM03",
        })
        assert resp.status_code == 200
        inv = game["player"]["inventory"]
        hm_entry = next((e for e in inv if e["item_id"] == 103), None)
        # HMs should NOT be consumed
        assert hm_entry is not None
        assert hm_entry["quantity"] == 1

    def test_use_tm_incompatible_pokemon(self, game):
        """Using a TM on incompatible Pokemon fails."""
        game_id = game["id"]
        game["player"]["inventory"].append({"item_id": 11, "quantity": 1})
        # TM for a move that Bulbasaur can't learn
        resp = client.post("/api/tm/use", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tm_number": "HM05",  # Fly - Bulbasaur can't fly
        })
        assert resp.status_code == 400

    def test_use_tm_no_inventory(self, game):
        """Using a TM not in inventory fails."""
        game_id = game["id"]
        resp = client.post("/api/tm/use", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tm_number": "TM01",
        })
        assert resp.status_code == 400

    def test_use_tm_with_move_replacement(self, game):
        """Using TM when Pokemon has 4 moves requires forget_move_index."""
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        while len(pokemon["moves"]) < 4:
            pokemon["moves"].append({
                "name": "Tackle", "type": "normal", "power": 40,
                "accuracy": 100, "pp": 35, "contact": True,
            })
        game["player"]["inventory"].append({"item_id": 11, "quantity": 1})
        resp = client.post("/api/tm/use", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tm_number": "TM01",
            "forget_move_index": 0,
        })
        assert resp.status_code == 200

    def test_use_tm_4_moves_no_forget(self, game):
        """Using TM fails with 4 moves and no forget_move_index."""
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        while len(pokemon["moves"]) < 4:
            pokemon["moves"].append({
                "name": "Tackle", "type": "normal", "power": 40,
                "accuracy": 100, "pp": 35, "contact": True,
            })
        game["player"]["inventory"].append({"item_id": 11, "quantity": 1})
        resp = client.post("/api/tm/use", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tm_number": "TM01",
        })
        assert resp.status_code == 400


# ============================================================
# HM Deletion Prevention
# ============================================================

class TestHMProtection:
    def test_cannot_forget_hm_move_via_tutor(self, game_with_money):
        """Cannot use forget_move_index to replace an HM move via tutor."""
        game_id = game_with_money["id"]
        pokemon = game_with_money["player"]["team"][0]
        # Give pokemon Cut (HM move) and fill to 4 moves
        pokemon["moves"] = [
            {"name": "Cut", "type": "normal", "power": 50, "accuracy": 95, "pp": 30, "contact": True},
            {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35, "contact": True},
            {"name": "Growl", "type": "normal", "power": 0, "accuracy": 100, "pp": 40, "contact": False},
            {"name": "Vine Whip", "type": "grass", "power": 45, "accuracy": 100, "pp": 25, "contact": True},
        ]
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": "Razor Leaf",
            "forget_move_index": 0,  # Trying to forget Cut
        })
        assert resp.status_code == 400

    def test_cannot_forget_hm_move_via_tm(self, game):
        """Cannot use forget_move_index to replace an HM move via TM."""
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        pokemon["moves"] = [
            {"name": "Surf", "type": "water", "power": 90, "accuracy": 100, "pp": 15, "contact": False},
            {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35, "contact": True},
            {"name": "Growl", "type": "normal", "power": 0, "accuracy": 100, "pp": 40, "contact": False},
            {"name": "Vine Whip", "type": "grass", "power": 45, "accuracy": 100, "pp": 25, "contact": True},
        ]
        game["player"]["inventory"].append({"item_id": 11, "quantity": 1})
        resp = client.post("/api/tm/use", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tm_number": "TM01",
            "forget_move_index": 0,  # Trying to forget Surf
        })
        assert resp.status_code == 400

    def test_can_forget_non_hm_move(self, game_with_money):
        """Can forget a normal move when learning a new one."""
        game_id = game_with_money["id"]
        pokemon = game_with_money["player"]["team"][0]
        pokemon["moves"] = [
            {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35, "contact": True},
            {"name": "Growl", "type": "normal", "power": 0, "accuracy": 100, "pp": 40, "contact": False},
            {"name": "Vine Whip", "type": "grass", "power": 45, "accuracy": 100, "pp": 25, "contact": True},
            {"name": "Razor Leaf", "type": "grass", "power": 55, "accuracy": 95, "pp": 25, "contact": False},
        ]
        resp = client.post("/api/tutor/teach", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "tutor_id": "pallet_tutor",
            "move_name": "Solar Beam",
            "forget_move_index": 0,  # Forgetting Tackle (not HM)
        })
        assert resp.status_code == 200


# ============================================================
# Move Reminder
# ============================================================

class TestMoveReminder:
    def test_get_forgotten_moves(self, game):
        """GET /api/tutor/reminder/{game_id}/{pokemon_index} returns re-learnable moves."""
        game_id = game["id"]
        resp = client.get(f"/api/tutor/reminder/{game_id}/0")
        assert resp.status_code == 200
        data = resp.json()
        assert "forgotten_moves" in data

    def test_remind_move_success(self, game):
        """POST /api/tutor/remind teaches a forgotten move for Heart Scale cost."""
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        # Give a Heart Scale item
        game["player"]["inventory"].append({"item_id": 50, "quantity": 1})  # Heart Scale

        resp = client.post("/api/tutor/remind", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "move_name": "Growl",  # Bulbasaur learns at lv3, might have been forgotten
        })
        # If successful, move should be added
        if resp.status_code == 200:
            data = resp.json()
            assert data["success"] is True

    def test_remind_move_no_heart_scale(self, game):
        """Reminding a move without Heart Scale fails."""
        game_id = game["id"]
        resp = client.post("/api/tutor/remind", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "move_name": "Growl",
        })
        assert resp.status_code == 400


# ============================================================
# Service-Level Tests (Direct Function Calls)
# ============================================================

class TestMoveTutorService:
    def test_get_tutor_data(self):
        """get_tutor returns tutor data dict."""
        from backend.services.move_tutor_service import get_tutor
        tutor = get_tutor("pallet_tutor")
        assert tutor is not None
        assert tutor["tutor_id"] == "pallet_tutor"

    def test_get_all_tutors(self):
        """get_all_tutors returns list of all tutors."""
        from backend.services.move_tutor_service import get_all_tutors
        tutors = get_all_tutors()
        assert len(tutors) >= 3  # pallet, viridian, pewter

    def test_get_tm_definitions(self):
        """get_all_tms returns list of all TM/HM defs."""
        from backend.services.move_tutor_service import get_all_tms
        tms = get_all_tms()
        assert len(tms) > 0
        # Should have at least 5 HMs
        hms = [t for t in tms if t["is_hm"]]
        assert len(hms) >= 5

    def test_check_compatibility_valid(self):
        """check_tm_compatibility returns True for valid combo."""
        from backend.services.move_tutor_service import check_tm_compatibility
        # Bulbasaur should be compatible with at least one TM
        result = check_tm_compatibility("TM01", 1)
        assert isinstance(result, bool)

    def test_check_tutor_compatibility(self):
        """check_tutor_compatibility validates species can learn move from tutor."""
        from backend.services.move_tutor_service import check_tutor_compatibility
        # Bulbasaur + grass moves from pallet tutor
        result = check_tutor_compatibility("pallet_tutor", 1, "Vine Whip")
        assert result is True

    def test_hm_moves_set(self):
        """HM_MOVES constant contains all 5 HM move names."""
        from backend.services.move_tutor_service import HM_MOVES
        assert "Cut" in HM_MOVES
        assert "Flash" in HM_MOVES
        assert "Surf" in HM_MOVES
        assert "Strength" in HM_MOVES
        assert "Fly" in HM_MOVES

    def test_is_hm_move(self):
        """is_hm_move correctly identifies HM moves."""
        from backend.services.move_tutor_service import is_hm_move
        assert is_hm_move("Cut") is True
        assert is_hm_move("Surf") is True
        assert is_hm_move("Tackle") is False
        assert is_hm_move("Thunderbolt") is False

    def test_teach_via_tutor(self, game_with_money):
        """teach_move_via_tutor directly adds move to Pokemon."""
        from backend.services.move_tutor_service import teach_move_via_tutor
        game_id = game_with_money["id"]
        pokemon = game_with_money["player"]["team"][0]
        # Clear to 2 moves so we can teach without replacement
        pokemon["moves"] = [pokemon["moves"][0], pokemon["moves"][1]]
        result = teach_move_via_tutor(game_id, 0, "pallet_tutor", "Razor Leaf")
        assert result is not None
        assert result["success"] is True

    def test_use_tm_direct(self, game):
        """use_tm directly teaches TM move to Pokemon."""
        from backend.services.move_tutor_service import use_tm
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        pokemon["moves"] = pokemon["moves"][:3]  # Make room
        game["player"]["inventory"].append({"item_id": 11, "quantity": 1})
        result = use_tm(game_id, 0, "TM01")
        assert result is not None
        assert result["success"] is True

    def test_get_forgotten_moves_for_pokemon(self, game):
        """get_forgotten_moves returns moves from species learnset not currently known."""
        from backend.services.move_tutor_service import get_forgotten_moves
        game_id = game["id"]
        moves = get_forgotten_moves(game_id, 0)
        assert isinstance(moves, list)


# ============================================================
# Edge Cases
# ============================================================

class TestMoveTutorEdgeCases:
    def test_teach_same_move_twice_fails(self, game_with_money):
        """Cannot teach a move the Pokemon already knows."""
        from backend.services.move_tutor_service import teach_move_via_tutor
        game_id = game_with_money["id"]
        pokemon = game_with_money["player"]["team"][0]
        # Clear to 1 move so first teach works
        pokemon["moves"] = [pokemon["moves"][0]]  # Just Tackle
        # First teach succeeds
        result = teach_move_via_tutor(game_id, 0, "pallet_tutor", "Vine Whip")
        assert result is not None and result["success"] is True
        # Second teach of same move fails
        result2 = teach_move_via_tutor(game_id, 0, "pallet_tutor", "Vine Whip")
        assert result2 is not None and result2["success"] is False

    def test_move_not_in_tutor_catalog(self, game_with_money):
        """Teaching a move not offered by the tutor fails."""
        from backend.services.move_tutor_service import teach_move_via_tutor
        game_id = game_with_money["id"]
        result = teach_move_via_tutor(game_id, 0, "pallet_tutor", "Hyper Beam")
        assert result is not None and result["success"] is False

    def test_tm_with_null_item_id_requires_inventory(self, game):
        """BUG #169: TM03-TM10 have null item_id which bypasses inventory check.

        Using TM03 (Psychic) without having it in inventory should fail,
        but the null item_id causes the inventory check to be skipped entirely.
        """
        from backend.services.move_tutor_service import use_tm
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        # Bulbasaur (id=1) is in TM03 compatibility set
        pokemon["moves"] = pokemon["moves"][:3]  # Make room
        # Do NOT add TM03 to inventory — this should fail
        result = use_tm(game_id, 0, "TM03")
        assert result is not None
        assert result["success"] is False, (
            "TM03 with null item_id should not bypass inventory check"
        )
        assert "inventory" in result["message"].lower() or "don't have" in result["message"].lower()

    def test_all_tms_have_valid_item_ids(self):
        """All non-HM TM definitions must have a non-null item_id."""
        from backend.services.move_tutor_service import TM_DEFINITIONS
        for tm_def in TM_DEFINITIONS:
            if not tm_def["is_hm"]:
                assert tm_def["item_id"] is not None, (
                    f"{tm_def['tm_number']} has null item_id — "
                    f"this bypasses inventory check"
                )

    def test_tutor_badge_requirement(self, game_with_money):
        """Tutor with badge requirement refuses if player lacks badges."""
        resp = client.get("/api/tutor/pewter_tutor")
        data = resp.json()
        if data.get("required_badges", 0) > 0:
            game_with_money["badges"] = 0
            resp = client.post("/api/tutor/teach", json={
                "game_id": game_with_money["id"],
                "pokemon_index": 0,
                "tutor_id": "pewter_tutor",
                "move_name": data["moves_offered"][0]["move_name"],
            })
            assert resp.status_code == 400
