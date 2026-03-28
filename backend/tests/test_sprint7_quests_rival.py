"""Tests for Sprint 7: Quest, Story Flags, Rival, and Progression system."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import _games, create_game_with_starter
from backend.services.quest_service import _player_quests, _story_flags
from backend.services.rival_service import _rival_data

client = TestClient(app)


def _make_game(name="TestPlayer", starter_id=1):
    """Create a game with a starter Pokemon for testing."""
    starter = {
        "id": starter_id,
        "name": "Bulbasaur" if starter_id == 1 else "Charmander" if starter_id == 4 else "Squirtle",
        "types": ["grass", "poison"] if starter_id == 1 else ["fire"] if starter_id == 4 else ["water"],
        "stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
        "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
        "sprite": "bulbasaur.png",
        "level": 5,
        "ability_id": "overgrow",
    }
    return create_game_with_starter(name, starter)


def _cleanup(game_id):
    """Clean up in-memory state for a game."""
    _games.pop(game_id, None)
    _player_quests.pop(game_id, None)
    _story_flags.pop(game_id, None)
    _rival_data.pop(game_id, None)


# ---- Quest Endpoints ----

class TestQuestRoutes:
    def test_list_quests(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/quests/{gid}")
        assert resp.status_code == 200
        quests = resp.json()
        assert len(quests) >= 5
        # First quest should be active (no prerequisites)
        new_adventure = [q for q in quests if q["id"] == "new_adventure"]
        assert len(new_adventure) == 1
        assert new_adventure[0]["status"] == "active"
        _cleanup(gid)

    def test_quest_detail(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/quests/{gid}/new_adventure")
        assert resp.status_code == 200
        quest = resp.json()
        assert quest["name"] == "A New Adventure"
        assert len(quest["objectives"]) == 1
        _cleanup(gid)

    def test_quest_detail_not_found(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/quests/{gid}/nonexistent_quest")
        assert resp.status_code == 404
        _cleanup(gid)

    def test_check_progress_advances_objective(self):
        game = _make_game()
        gid = game["id"]
        # Trigger the "choose_starter" objective
        resp = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "collect_item",
            "event_data": {"item_id": "starter"},
        })
        assert resp.status_code == 200
        result = resp.json()
        # Should have completed new_adventure
        assert len(result["completed_quests"]) == 1
        assert result["completed_quests"][0]["id"] == "new_adventure"
        _cleanup(gid)

    def test_check_progress_unlocks_dependent_quests(self):
        game = _make_game()
        gid = game["id"]
        # Complete new_adventure
        resp = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "collect_item",
            "event_data": {"item_id": "starter"},
        })
        result = resp.json()
        # oaks_parcel should unlock (prerequisite: new_adventure)
        # rival_showdown_1 requires oaks_parcel, so it stays locked
        newly_active_ids = [q["id"] for q in result["newly_active_quests"]]
        assert "oaks_parcel" in newly_active_ids
        _cleanup(gid)

    def test_complete_quest_manual(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/quests/{gid}/new_adventure/complete")
        assert resp.status_code == 200
        result = resp.json()
        assert result["quest"]["status"] == "completed"
        assert result["rewards_given"]["money"] == 500
        assert "oaks_parcel" in result["newly_unlocked_quests"]
        _cleanup(gid)

    def test_complete_quest_already_completed(self):
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        resp = client.post(f"/api/quests/{gid}/new_adventure/complete")
        assert resp.status_code == 400
        _cleanup(gid)

    def test_complete_quest_gives_money(self):
        game = _make_game()
        gid = game["id"]
        money_before = game["player"].get("money", 0)
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        game_after = _games[gid]
        money_after = game_after["player"].get("money", 0)
        assert money_after == money_before + 500
        _cleanup(gid)

    def test_complete_quest_gives_items(self):
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        game_after = _games[gid]
        inventory = game_after["player"].get("inventory", [])
        pokeball = [i for i in inventory if i.get("item_id") == 7]
        assert len(pokeball) == 1
        assert pokeball[0]["quantity"] == 5
        _cleanup(gid)

    def test_quest_prerequisite_chain(self):
        game = _make_game()
        gid = game["id"]
        # boulder_badge requires oaks_parcel which requires new_adventure
        resp = client.get(f"/api/quests/{gid}/boulder_badge")
        assert resp.json()["status"] == "locked"

        # Complete new_adventure
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        resp = client.get(f"/api/quests/{gid}/oaks_parcel")
        assert resp.json()["status"] == "active"
        resp = client.get(f"/api/quests/{gid}/boulder_badge")
        assert resp.json()["status"] == "locked"

        # Complete oaks_parcel
        client.post(f"/api/quests/{gid}/oaks_parcel/complete")
        resp = client.get(f"/api/quests/{gid}/boulder_badge")
        assert resp.json()["status"] == "active"
        _cleanup(gid)


# ---- Story Flag Endpoints ----

class TestStoryFlagRoutes:
    def test_get_flags_empty(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/flags/{gid}")
        assert resp.status_code == 200
        assert resp.json() == {}
        _cleanup(gid)

    def test_set_and_get_flag(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/flags/set", json={
            "game_id": gid,
            "flag_name": "has_starter",
            "value": True,
        })
        assert resp.status_code == 200
        assert resp.json()["has_starter"] is True

        resp = client.get(f"/api/flags/{gid}/has_starter")
        assert resp.json()["value"] is True
        _cleanup(gid)

    def test_get_unset_flag(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/flags/{gid}/nonexistent")
        assert resp.status_code == 200
        assert resp.json()["value"] is False
        _cleanup(gid)

    def test_quest_completion_sets_flags(self):
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        resp = client.get(f"/api/flags/{gid}/has_starter")
        assert resp.json()["value"] is True
        _cleanup(gid)


# ---- Area Gating ----

class TestAreaGating:
    def test_area_accessible_no_flag_required(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/quests/area-check", json={
            "game_id": gid,
            "map_id": "pallet_town",
        })
        assert resp.status_code == 200
        assert resp.json()["accessible"] is True
        _cleanup(gid)

    def test_area_blocked_by_flag(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/quests/area-check", json={
            "game_id": gid,
            "map_id": "route_2",
            "required_flag": "has_starter",
        })
        assert resp.json()["accessible"] is False
        assert "starter" in resp.json()["reason"].lower()
        _cleanup(gid)

    def test_area_accessible_after_flag_set(self):
        game = _make_game()
        gid = game["id"]
        client.post("/api/flags/set", json={
            "game_id": gid,
            "flag_name": "has_starter",
            "value": True,
        })
        resp = client.post("/api/quests/area-check", json={
            "game_id": gid,
            "map_id": "route_2",
            "required_flag": "has_starter",
        })
        assert resp.json()["accessible"] is True
        _cleanup(gid)


# ---- Rival Endpoints ----

class TestRivalRoutes:
    def test_init_rival_with_bulbasaur(self):
        game = _make_game(starter_id=1)
        gid = game["id"]
        resp = client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 1,
        })
        assert resp.status_code == 200
        rival = resp.json()
        assert rival["name"] == "Blue"
        assert rival["starter_species_id"] == 4  # Charmander counters Bulbasaur
        _cleanup(gid)

    def test_init_rival_with_charmander(self):
        game = _make_game(starter_id=4)
        gid = game["id"]
        resp = client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 4,
        })
        rival = resp.json()
        assert rival["starter_species_id"] == 7  # Squirtle counters Charmander
        _cleanup(gid)

    def test_init_rival_with_squirtle(self):
        game = _make_game(starter_id=7)
        gid = game["id"]
        resp = client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 7,
        })
        rival = resp.json()
        assert rival["starter_species_id"] == 1  # Bulbasaur counters Squirtle
        _cleanup(gid)

    def test_get_rival(self):
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 1,
        })
        resp = client.get(f"/api/rival/{gid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Blue"
        _cleanup(gid)

    def test_rival_battle_stage_1(self):
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 1,
        })
        resp = client.post("/api/rival/battle", json={
            "game_id": gid,
            "stage": 1,
        })
        assert resp.status_code == 200
        result = resp.json()
        assert result["rival_name"] == "Blue"
        assert result["battle_id"] is not None
        assert len(result["rival_team_preview"]) == 1
        assert result["rival_team_preview"][0] == "Charmander"
        _cleanup(gid)

    def test_rival_battle_stage_2(self):
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 1,
        })
        resp = client.post("/api/rival/battle", json={
            "game_id": gid,
            "stage": 2,
        })
        assert resp.status_code == 200
        result = resp.json()
        assert len(result["rival_team_preview"]) == 2
        # Should have evolved starter + Pidgeotto
        assert "Pidgeotto" in result["rival_team_preview"]
        _cleanup(gid)

    def test_rival_battle_stage_3(self):
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 1,
        })
        resp = client.post("/api/rival/battle", json={
            "game_id": gid,
            "stage": 3,
        })
        assert resp.status_code == 200
        result = resp.json()
        assert len(result["rival_team_preview"]) == 6
        _cleanup(gid)

    def test_rival_battle_no_game(self):
        resp = client.post("/api/rival/battle", json={
            "game_id": "nonexistent",
            "stage": 1,
        })
        assert resp.status_code == 404

    def test_rival_battle_complete_sets_flags(self):
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 1,
        })
        resp = client.post("/api/rival/battle-complete", json={
            "game_id": gid,
            "stage": 2,
        })
        assert resp.status_code == 200

        # Check that the story flag was set
        resp = client.get(f"/api/flags/{gid}/rival_defeated_route2")
        assert resp.json()["value"] is True
        _cleanup(gid)

    def test_rival_reward_money_scales(self):
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 1,
        })
        resp1 = client.post("/api/rival/battle", json={"game_id": gid, "stage": 1})
        resp2 = client.post("/api/rival/battle", json={"game_id": gid, "stage": 2})
        resp3 = client.post("/api/rival/battle", json={"game_id": gid, "stage": 3})
        assert resp1.json()["reward_money"] == 1000
        assert resp2.json()["reward_money"] == 1500
        assert resp3.json()["reward_money"] == 2000
        _cleanup(gid)
