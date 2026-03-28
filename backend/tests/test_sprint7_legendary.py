"""Tests for Sprint 7: Legendary Pokemon Data & Encounter System."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import _games, create_game_with_starter
from backend.services.legendary_service import LEGENDARY_DEFS, _legendary_status
from backend.services.quest_service import _player_quests, _story_flags

client = TestClient(app)


def _make_game(name="TestPlayer"):
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
    return create_game_with_starter(name, starter)


def _cleanup(game_id):
    _games.pop(game_id, None)
    _player_quests.pop(game_id, None)
    _story_flags.pop(game_id, None)
    _legendary_status.pop(game_id, None)


def _set_flags(game_id, flags):
    """Helper to set multiple story flags."""
    for flag in flags:
        client.post("/api/flags/set", json={"game_id": game_id, "flag_name": flag, "value": True})


# ---- Legendary Definitions ----

class TestLegendaryDefs:
    def test_three_legendaries_defined(self):
        assert len(LEGENDARY_DEFS) == 3
        assert 150 in LEGENDARY_DEFS  # Mewtwo
        assert 144 in LEGENDARY_DEFS  # Articuno
        assert 145 in LEGENDARY_DEFS  # Zapdos

    def test_mewtwo_stats(self):
        mewtwo = LEGENDARY_DEFS[150]
        assert mewtwo.name == "Mewtwo"
        assert mewtwo.level == 70
        assert mewtwo.catch_rate == 3
        assert mewtwo.types == ["psychic"]
        assert "badge_boulder" in mewtwo.required_flags

    def test_articuno_stats(self):
        articuno = LEGENDARY_DEFS[144]
        assert articuno.name == "Articuno"
        assert articuno.level == 50
        assert articuno.types == ["ice", "flying"]

    def test_zapdos_stats(self):
        zapdos = LEGENDARY_DEFS[145]
        assert zapdos.name == "Zapdos"
        assert zapdos.level == 50
        assert zapdos.types == ["electric", "flying"]


# ---- List Endpoint ----

class TestLegendaryList:
    def test_list_all_legendaries(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/legendary/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        names = {d["name"] for d in data}
        assert names == {"Mewtwo", "Articuno", "Zapdos"}
        _cleanup(gid)

    def test_list_shows_locked_without_flags(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/legendary/{gid}")
        data = resp.json()
        for entry in data:
            assert entry["status"] == "locked"
            assert entry["requirements_met"] is False
        _cleanup(gid)

    def test_list_shows_available_with_flags(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        resp = client.get(f"/api/legendary/{gid}")
        data = resp.json()
        articuno = [e for e in data if e["name"] == "Articuno"][0]
        assert articuno["status"] == "available"
        assert articuno["requirements_met"] is True
        _cleanup(gid)


# ---- Check Endpoint ----

class TestLegendaryCheck:
    def test_check_not_found(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/legendary/{gid}/999/check")
        assert resp.status_code == 404
        _cleanup(gid)

    def test_check_locked(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/legendary/{gid}/144/check")
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False
        assert data["requirements_met"] is False
        assert "badge_cascade" in data["missing_flags"]
        _cleanup(gid)

    def test_check_available(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        resp = client.get(f"/api/legendary/{gid}/144/check")
        data = resp.json()
        assert data["available"] is True
        assert data["requirements_met"] is True
        assert data["already_caught"] is False
        assert data["already_fainted"] is False
        _cleanup(gid)

    def test_check_after_caught(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        client.post(f"/api/legendary/{gid}/144/caught")
        resp = client.get(f"/api/legendary/{gid}/144/check")
        data = resp.json()
        assert data["available"] is False
        assert data["already_caught"] is True
        _cleanup(gid)

    def test_check_after_fainted(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        client.post(f"/api/legendary/{gid}/144/fainted")
        resp = client.get(f"/api/legendary/{gid}/144/check")
        data = resp.json()
        assert data["available"] is False
        assert data["already_fainted"] is True
        _cleanup(gid)


# ---- Encounter Endpoint ----

class TestLegendaryEncounter:
    def test_encounter_without_flags_fails(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/legendary/{gid}/144/encounter")
        assert resp.status_code == 400
        _cleanup(gid)

    def test_encounter_with_flags_succeeds(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        resp = client.post(f"/api/legendary/{gid}/144/encounter")
        assert resp.status_code == 200
        data = resp.json()
        assert data["legendary_name"] == "Articuno"
        assert data["legendary_level"] == 50
        assert data["battle_id"] is not None
        _cleanup(gid)

    def test_encounter_already_caught_fails(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        client.post(f"/api/legendary/{gid}/144/caught")
        resp = client.post(f"/api/legendary/{gid}/144/encounter")
        assert resp.status_code == 400
        _cleanup(gid)

    def test_encounter_already_fainted_fails(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        client.post(f"/api/legendary/{gid}/144/fainted")
        resp = client.post(f"/api/legendary/{gid}/144/encounter")
        assert resp.status_code == 400
        _cleanup(gid)

    def test_encounter_nonexistent_legendary(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/legendary/{gid}/999/encounter")
        assert resp.status_code == 400
        _cleanup(gid)

    def test_encounter_mewtwo_requires_both_badges(self):
        game = _make_game()
        gid = game["id"]
        # Only one badge — should fail
        _set_flags(gid, ["badge_boulder"])
        resp = client.post(f"/api/legendary/{gid}/150/encounter")
        assert resp.status_code == 400
        # Both badges — should succeed
        _set_flags(gid, ["badge_cascade"])
        resp = client.post(f"/api/legendary/{gid}/150/encounter")
        assert resp.status_code == 200
        assert resp.json()["legendary_name"] == "Mewtwo"
        _cleanup(gid)


# ---- Status Transitions ----

class TestLegendaryStatusTransitions:
    def test_caught_status(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/legendary/{gid}/150/caught")
        assert resp.status_code == 200
        resp = client.get(f"/api/legendary/{gid}/150/check")
        assert resp.json()["already_caught"] is True
        _cleanup(gid)

    def test_fainted_status(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/legendary/{gid}/150/fainted")
        assert resp.status_code == 200
        resp = client.get(f"/api/legendary/{gid}/150/check")
        assert resp.json()["already_fainted"] is True
        _cleanup(gid)

    def test_fled_resets_to_available(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_boulder", "badge_cascade"])
        # Start encounter
        client.post(f"/api/legendary/{gid}/150/encounter")
        # Flee
        client.post(f"/api/legendary/{gid}/150/fled")
        # Should be available again
        resp = client.get(f"/api/legendary/{gid}/150/check")
        data = resp.json()
        assert data["available"] is True
        assert data["already_caught"] is False
        assert data["already_fainted"] is False
        _cleanup(gid)

    def test_encounter_sets_in_battle(self):
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        client.post(f"/api/legendary/{gid}/144/encounter")
        # Second encounter should fail (in_battle)
        resp = client.post(f"/api/legendary/{gid}/144/encounter")
        assert resp.status_code == 400
        _cleanup(gid)


# ---- Master Ball Item ----

class TestMasterBall:
    def test_master_ball_exists_in_items(self):
        resp = client.get("/api/items")
        assert resp.status_code == 200
        items = resp.json()
        master = [i for i in items if i["name"] == "Master Ball"]
        assert len(master) == 1
        assert master[0]["category"] == "pokeball"

    def test_master_ball_not_in_shops(self):
        """Master Ball should not be purchasable in any shop."""
        resp = client.get("/api/items/shop/viridian_pokemart")
        if resp.status_code == 200:
            shop = resp.json()
            item_ids = [i["item_id"] for i in shop.get("items", [])]
            assert 10 not in item_ids  # Master Ball ID


# ---- Move Data ----

class TestLegendaryMoves:
    def test_psychic_move_exists(self):
        from backend.services.encounter_service import get_move_data
        move = get_move_data("Psychic")
        assert move is not None
        assert move["type"] == "psychic"
        assert move["power"] == 90

    def test_recover_move_exists(self):
        from backend.services.encounter_service import get_move_data
        move = get_move_data("Recover")
        assert move is not None
        assert move["power"] == 0

    def test_drill_peck_move_exists(self):
        from backend.services.encounter_service import get_move_data
        move = get_move_data("Drill Peck")
        assert move is not None
        assert move["type"] == "flying"
        assert move["power"] == 80

    def test_barrier_move_exists(self):
        from backend.services.encounter_service import get_move_data
        move = get_move_data("Barrier")
        assert move is not None

    def test_mist_move_exists(self):
        from backend.services.encounter_service import get_move_data
        move = get_move_data("Mist")
        assert move is not None
