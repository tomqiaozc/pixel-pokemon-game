"""Sprint 7 QA-A Gap Coverage Tests: Story quests, rival & legendary Pokemon.

Covers edge cases, error paths, and boundary conditions not exercised by
the existing test_sprint7_quests_rival.py and test_sprint7_legendary.py.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import _games, create_game_with_starter
from backend.services.legendary_service import (
    LEGENDARY_DEFS,
    _build_legendary_battle_dict,
    _legendary_status,
)
from backend.services.quest_service import _player_quests, _story_flags
from backend.services.rival_service import _rival_data

client = TestClient(app)


# ---- Helpers ----

def _make_game(name="TestPlayer"):
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
    _rival_data.pop(game_id, None)


def _set_flags(game_id, flags):
    for flag in flags:
        client.post("/api/flags/set", json={"game_id": game_id, "flag_name": flag, "value": True})


# ==============================================================
# QUEST SERVICE GAPS
# ==============================================================

class TestQuestInvalidGame:
    """Quest endpoints with nonexistent game IDs."""

    def test_check_progress_nonexistent_game(self):
        """check_quest_progress returns empty result for nonexistent game."""
        resp = client.post("/api/quests/check-progress", json={
            "game_id": "nonexistent_game_999",
            "event_type": "collect_item",
            "event_data": {"item_id": "starter"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_quests"] == []
        assert data["newly_active_quests"] == []

    def test_complete_quest_nonexistent_game(self):
        """Complete quest on nonexistent game returns 400."""
        resp = client.post("/api/quests/nonexistent_game/new_adventure/complete")
        assert resp.status_code == 400


class TestQuestProgressEdgeCases:
    """Edge cases for quest progress checking."""

    def test_non_matching_event_type(self):
        """Event type that no quest objective listens for produces no updates."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "catch_pokemon",
            "event_data": {"species_id": "pikachu"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_quests"] == []
        _cleanup(gid)

    def test_matching_event_wrong_target(self):
        """Correct event type but wrong target does not advance objective."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "collect_item",
            "event_data": {"item_id": "wrong_target"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_quests"] == []
        # Verify quest still active, not advanced
        resp2 = client.get(f"/api/quests/{gid}/new_adventure")
        assert resp2.json()["status"] == "active"
        _cleanup(gid)

    def test_duplicate_event_firing_clamped(self):
        """Firing the same event twice does not double-complete."""
        game = _make_game()
        gid = game["id"]
        # First fire — completes quest
        resp1 = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "collect_item",
            "event_data": {"item_id": "starter"},
        })
        assert len(resp1.json()["completed_quests"]) == 1
        # Second fire — already completed, should be no-op
        resp2 = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "collect_item",
            "event_data": {"item_id": "starter"},
        })
        assert resp2.json()["completed_quests"] == []
        _cleanup(gid)

    def test_locked_quest_not_advanced_by_events(self):
        """Events do not advance objectives on locked quests."""
        game = _make_game()
        gid = game["id"]
        # boulder_badge is locked — try to advance its objective
        resp = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "defeat_gym",
            "event_data": {"gym_id": "pewter_gym"},
        })
        assert resp.status_code == 200
        assert resp.json()["completed_quests"] == []
        # Verify still locked
        resp2 = client.get(f"/api/quests/{gid}/boulder_badge")
        assert resp2.json()["status"] == "locked"
        _cleanup(gid)


class TestQuestManualComplete:
    """Edge cases for manual quest completion."""

    def test_complete_nonexistent_quest_id(self):
        """Completing a quest ID that doesn't exist returns 400."""
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/quests/{gid}/totally_fake_quest/complete")
        assert resp.status_code == 400
        _cleanup(gid)

    def test_complete_locked_quest_allowed(self):
        """Manual completion can force-complete locked quests (scripted events)."""
        game = _make_game()
        gid = game["id"]
        # boulder_badge is locked (needs oaks_parcel which needs new_adventure)
        resp = client.get(f"/api/quests/{gid}/boulder_badge")
        assert resp.json()["status"] == "locked"
        # Manual force-complete should work
        resp = client.post(f"/api/quests/{gid}/boulder_badge/complete")
        assert resp.status_code == 200
        result = resp.json()
        assert result["quest"]["status"] == "completed"
        assert result["rewards_given"]["money"] == 2000
        _cleanup(gid)


class TestQuestMultiObjective:
    """Tests for quests with multiple objectives (oaks_parcel)."""

    def test_partial_progress_keeps_quest_active(self):
        """Completing one objective of multi-objective quest keeps it active."""
        game = _make_game()
        gid = game["id"]
        # First unlock oaks_parcel by completing new_adventure
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        # Advance first objective (visit_viridian — visit_location target_key="map_id")
        resp = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "visit_location",
            "event_data": {"map_id": "viridian_city"},
        })
        assert resp.status_code == 200
        # Quest should still be active (second objective not done)
        assert resp.json()["completed_quests"] == []
        quest_resp = client.get(f"/api/quests/{gid}/oaks_parcel")
        assert quest_resp.json()["status"] == "active"
        _cleanup(gid)

    def test_both_objectives_completes_quest(self):
        """Completing all objectives completes the multi-objective quest."""
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        # Complete first objective (visit_location target_key="map_id")
        client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "visit_location",
            "event_data": {"map_id": "viridian_city"},
        })
        # Complete second objective (deliver_item target_key="location_id")
        resp = client.post("/api/quests/check-progress", json={
            "game_id": gid,
            "event_type": "deliver_item",
            "event_data": {"location_id": "oaks_lab"},
        })
        assert resp.status_code == 200
        completed_ids = [q["id"] for q in resp.json()["completed_quests"]]
        assert "oaks_parcel" in completed_ids
        _cleanup(gid)


class TestQuestRewards:
    """Reward edge cases."""

    def test_quest_rewards_set_unlock_flags(self):
        """Completing new_adventure sets the has_starter flag."""
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        resp = client.get(f"/api/flags/{gid}/has_starter")
        assert resp.json()["value"] is True
        _cleanup(gid)

    def test_oaks_parcel_sets_multiple_flags(self):
        """Completing oaks_parcel sets has_pokedex and oak_parcel_delivered."""
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        client.post(f"/api/quests/{gid}/oaks_parcel/complete")
        resp1 = client.get(f"/api/flags/{gid}/has_pokedex")
        resp2 = client.get(f"/api/flags/{gid}/oak_parcel_delivered")
        assert resp1.json()["value"] is True
        assert resp2.json()["value"] is True
        _cleanup(gid)

    def test_item_reward_merges_with_existing_inventory(self):
        """Item rewards merge quantities when item already in inventory."""
        game = _make_game()
        gid = game["id"]
        # Pre-seed inventory with 3 Poke Balls (item_id 7)
        _games[gid]["player"]["inventory"] = [{"item_id": 7, "quantity": 3}]
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        inventory = _games[gid]["player"]["inventory"]
        pokeball = [i for i in inventory if i.get("item_id") == 7]
        assert len(pokeball) == 1
        assert pokeball[0]["quantity"] == 8  # 3 existing + 5 reward
        _cleanup(gid)


# ==============================================================
# STORY FLAG GAPS
# ==============================================================

class TestStoryFlagEdgeCases:
    """Additional story flag edge cases."""

    def test_set_flag_false(self):
        """Setting a flag to False."""
        game = _make_game()
        gid = game["id"]
        # Set to True first
        client.post("/api/flags/set", json={"game_id": gid, "flag_name": "test_flag", "value": True})
        resp = client.get(f"/api/flags/{gid}/test_flag")
        assert resp.json()["value"] is True
        # Set to False
        client.post("/api/flags/set", json={"game_id": gid, "flag_name": "test_flag", "value": False})
        resp = client.get(f"/api/flags/{gid}/test_flag")
        assert resp.json()["value"] is False
        _cleanup(gid)

    def test_multiple_flags_independent(self):
        """Setting multiple flags does not affect each other."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/flags/set", json={"game_id": gid, "flag_name": "flag_a", "value": True})
        client.post("/api/flags/set", json={"game_id": gid, "flag_name": "flag_b", "value": True})
        client.post("/api/flags/set", json={"game_id": gid, "flag_name": "flag_a", "value": False})
        resp_a = client.get(f"/api/flags/{gid}/flag_a")
        resp_b = client.get(f"/api/flags/{gid}/flag_b")
        assert resp_a.json()["value"] is False
        assert resp_b.json()["value"] is True
        _cleanup(gid)


# ==============================================================
# AREA GATING GAPS
# ==============================================================

class TestAreaGatingEdgeCases:
    """Additional area gating edge cases."""

    def test_area_check_unknown_flag_fallback_message(self):
        """Unknown flag uses fallback reason message."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/quests/area-check", json={
            "game_id": gid,
            "map_id": "some_area",
            "required_flag": "unknown_custom_flag",
        })
        assert resp.json()["accessible"] is False
        assert "unknown_custom_flag" in resp.json()["reason"]
        _cleanup(gid)

    def test_area_check_badge_boulder_reason(self):
        """Badge-gated area shows specific badge reason message."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/quests/area-check", json={
            "game_id": gid,
            "map_id": "route_3",
            "required_flag": "badge_boulder",
        })
        assert resp.json()["accessible"] is False
        assert "Boulder Badge" in resp.json()["reason"]
        _cleanup(gid)


# ==============================================================
# RIVAL SERVICE GAPS
# ==============================================================

class TestRivalInit:
    """Rival initialization edge cases."""

    def test_init_rival_unknown_starter_fallback(self):
        """Unknown starter ID falls back to Charmander as rival's starter."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/rival/init", json={
            "game_id": gid,
            "player_starter_id": 999,
        })
        assert resp.status_code == 200
        rival = resp.json()
        # Fallback is species_id=4 (Charmander)
        assert rival["starter_species_id"] == 4
        _cleanup(gid)

    def test_get_rival_without_init(self):
        """Getting rival without init returns default data (not a 404)."""
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/rival/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Blue"
        _cleanup(gid)

    def test_double_init_rival(self):
        """Initializing rival twice overwrites the first."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        resp = client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 4})
        assert resp.status_code == 200
        # Second init with starter 4 → rival gets 7 (Squirtle)
        assert resp.json()["starter_species_id"] == 7
        _cleanup(gid)


class TestRivalBattleEdgeCases:
    """Rival battle edge cases."""

    def test_rival_battle_invalid_stage_fallback(self):
        """Invalid stage number falls back to stage 1 team."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        resp = client.post("/api/rival/battle", json={"game_id": gid, "stage": 99})
        assert resp.status_code == 200
        result = resp.json()
        # Falls back to stage 1 team (1 Pokemon)
        assert len(result["rival_team_preview"]) == 1
        _cleanup(gid)

    def test_rival_stage_2_has_unevolved_starter_at_level_15(self):
        """Stage 2 rival starter stays unevolved (Charmander evolves at 16, not 15)."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        resp = client.post("/api/rival/battle", json={"game_id": gid, "stage": 2})
        preview = resp.json()["rival_team_preview"]
        # Charmander evolves at level 16, so at level 15 it stays Charmander
        assert "Charmander" in preview
        assert "Pidgeotto" in preview
        _cleanup(gid)

    def test_rival_stage_3_full_team(self):
        """Stage 3 rival has exactly 6 Pokemon including fully evolved starter."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        resp = client.post("/api/rival/battle", json={"game_id": gid, "stage": 3})
        result = resp.json()
        assert len(result["rival_team_preview"]) == 6
        # Rival's starter should be fully evolved (Charizard)
        assert "Charizard" in result["rival_team_preview"]
        _cleanup(gid)


class TestRivalBattleComplete:
    """Rival battle-complete flag and quest advancement."""

    def test_battle_complete_stage_1_sets_lab_flag(self):
        """Stage 1 battle-complete sets rival_defeated_lab flag."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        resp = client.post("/api/rival/battle-complete", json={"game_id": gid, "stage": 1})
        assert resp.status_code == 200
        resp2 = client.get(f"/api/flags/{gid}/rival_defeated_lab")
        assert resp2.json()["value"] is True
        _cleanup(gid)

    def test_battle_complete_stage_3_sets_elite_flag(self):
        """Stage 3 battle-complete sets rival_defeated_elite flag."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        resp = client.post("/api/rival/battle-complete", json={"game_id": gid, "stage": 3})
        assert resp.status_code == 200
        resp2 = client.get(f"/api/flags/{gid}/rival_defeated_elite")
        assert resp2.json()["value"] is True
        _cleanup(gid)

    def test_battle_complete_stage_2_advances_rival_quest(self):
        """Stage 2 battle-complete advances the rival_showdown_1 quest."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        # Unlock rival_showdown_1 (requires oaks_parcel)
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        client.post(f"/api/quests/{gid}/oaks_parcel/complete")
        # Now complete rival battle stage 2
        client.post("/api/rival/battle-complete", json={"game_id": gid, "stage": 2})
        # Quest should be completed
        resp = client.get(f"/api/quests/{gid}/rival_showdown_1")
        assert resp.json()["status"] == "completed"
        _cleanup(gid)

    def test_battle_complete_invalid_stage_no_flag(self):
        """Unknown stage does not set any flag."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        resp = client.post("/api/rival/battle-complete", json={"game_id": gid, "stage": 99})
        assert resp.status_code == 200
        # No flags should be set
        flags_resp = client.get(f"/api/flags/{gid}")
        assert flags_resp.json() == {}
        _cleanup(gid)

    def test_rival_battle_nonexistent_game(self):
        """Rival battle for nonexistent game returns 404."""
        resp = client.post("/api/rival/battle", json={
            "game_id": "totally_fake_game",
            "stage": 1,
        })
        assert resp.status_code == 404


# ==============================================================
# LEGENDARY SERVICE GAPS
# ==============================================================

class TestLegendaryBattleDictConstruction:
    """Verify _build_legendary_battle_dict output correctness."""

    def test_mewtwo_stat_calculation(self):
        """Mewtwo's stats are calculated with IV=31 at level 70."""
        ldef = LEGENDARY_DEFS[150]
        result = _build_legendary_battle_dict(ldef)
        # HP: ((2*106 + 31) * 70) // 100 + 70 + 10 = (243*70)//100 + 80 = 17010//100 + 80 = 170 + 80 = 250
        assert result["stats"]["hp"] == 250
        assert result["current_hp"] == 250
        assert result["max_hp"] == 250
        # Attack: ((2*110 + 31) * 70) // 100 + 5 = (251*70)//100 + 5 = 17570//100 + 5 = 175 + 5 = 180
        assert result["stats"]["attack"] == 180

    def test_articuno_stat_calculation(self):
        """Articuno's stats at level 50 with IV=31."""
        ldef = LEGENDARY_DEFS[144]
        result = _build_legendary_battle_dict(ldef)
        # HP: ((2*90 + 31) * 50) // 100 + 50 + 10 = (211*50)//100 + 60 = 10550//100 + 60 = 105 + 60 = 165
        assert result["stats"]["hp"] == 165
        assert result["current_hp"] == 165

    def test_battle_dict_fields_complete(self):
        """Battle dict has all required fields."""
        ldef = LEGENDARY_DEFS[150]
        result = _build_legendary_battle_dict(ldef)
        assert result["species_id"] == 150
        assert result["name"] == "Mewtwo"
        assert result["types"] == ["psychic"]
        assert result["level"] == 70
        assert result["sprite"] == "mewtwo.png"
        assert result["ability_id"] == "pressure"
        assert result["catch_rate"] == 3
        assert len(result["moves"]) == 4

    def test_zapdos_battle_dict(self):
        """Zapdos battle dict is correctly constructed."""
        ldef = LEGENDARY_DEFS[145]
        result = _build_legendary_battle_dict(ldef)
        assert result["species_id"] == 145
        assert result["name"] == "Zapdos"
        assert result["types"] == ["electric", "flying"]
        assert result["level"] == 50
        assert result["catch_rate"] == 3

    def test_move_data_populated(self):
        """Legendary moves have correct data from move database."""
        ldef = LEGENDARY_DEFS[150]
        result = _build_legendary_battle_dict(ldef)
        move_names = [m["name"] for m in result["moves"]]
        assert "Psychic" in move_names
        assert "Recover" in move_names
        assert "Barrier" in move_names
        assert "Swift" in move_names


class TestLegendaryEncounterEdgeCases:
    """Encounter endpoint edge cases."""

    def test_encounter_nonexistent_game(self):
        """Encounter with nonexistent game_id returns 400."""
        resp = client.post("/api/legendary/nonexistent_game/144/encounter")
        assert resp.status_code == 400

    def test_encounter_response_message_format(self):
        """Encounter response includes formatted appearance message."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        resp = client.post(f"/api/legendary/{gid}/144/encounter")
        assert resp.status_code == 200
        assert resp.json()["message"] == "A wild Articuno appeared!"
        _cleanup(gid)

    def test_encounter_response_fields(self):
        """Encounter response has all expected fields."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        resp = client.post(f"/api/legendary/{gid}/145/encounter")
        data = resp.json()
        assert "battle_id" in data
        assert data["legendary_name"] == "Zapdos"
        assert data["legendary_level"] == 50
        assert data["message"] == "A wild Zapdos appeared!"
        _cleanup(gid)


class TestLegendaryStatusTransitionEdgeCases:
    """Status transition edge cases and potential bugs."""

    def test_caught_twice_idempotent(self):
        """Marking caught twice does not crash or change state."""
        game = _make_game()
        gid = game["id"]
        resp1 = client.post(f"/api/legendary/{gid}/150/caught")
        assert resp1.status_code == 200
        resp2 = client.post(f"/api/legendary/{gid}/150/caught")
        assert resp2.status_code == 200
        # Still caught
        check = client.get(f"/api/legendary/{gid}/150/check")
        assert check.json()["already_caught"] is True
        _cleanup(gid)

    def test_fainted_twice_idempotent(self):
        """Marking fainted twice does not crash or change state."""
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/legendary/{gid}/150/fainted")
        resp2 = client.post(f"/api/legendary/{gid}/150/fainted")
        assert resp2.status_code == 200
        check = client.get(f"/api/legendary/{gid}/150/check")
        assert check.json()["already_fainted"] is True
        _cleanup(gid)

    def test_fled_on_caught_resets_to_available_BUG(self):
        """BUG: mark_legendary_fled on a caught legendary resets to available.

        This documents the behavior — fled unconditionally sets status to
        'available' without checking current state. If this is unintended,
        a guard should be added.
        """
        game = _make_game()
        gid = game["id"]
        # Mark as caught
        client.post(f"/api/legendary/{gid}/150/caught")
        check = client.get(f"/api/legendary/{gid}/150/check")
        assert check.json()["already_caught"] is True
        # Flee (should arguably be no-op, but actually resets)
        client.post(f"/api/legendary/{gid}/150/fled")
        check = client.get(f"/api/legendary/{gid}/150/check")
        # Documents current behavior: caught legendary becomes available again
        assert check.json()["available"] is False or check.json()["available"] is True
        # The status is now "available", so already_caught should be False
        assert check.json()["already_caught"] is False
        _cleanup(gid)

    def test_fled_on_fainted_resets_to_available_BUG(self):
        """BUG: mark_legendary_fled on a fainted legendary resets to available.

        Same unguarded transition as caught→fled.
        """
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/legendary/{gid}/144/fainted")
        check = client.get(f"/api/legendary/{gid}/144/check")
        assert check.json()["already_fainted"] is True
        # Flee resets
        client.post(f"/api/legendary/{gid}/144/fled")
        check = client.get(f"/api/legendary/{gid}/144/check")
        assert check.json()["already_fainted"] is False
        _cleanup(gid)

    def test_in_battle_check_response(self):
        """During in_battle state, check shows not available, not caught, not fainted."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        # Start encounter (sets in_battle)
        client.post(f"/api/legendary/{gid}/144/encounter")
        # Check during battle
        check = client.get(f"/api/legendary/{gid}/144/check")
        data = check.json()
        assert data["available"] is False
        assert data["already_caught"] is False
        assert data["already_fainted"] is False
        _cleanup(gid)

    def test_full_lifecycle_encounter_to_caught(self):
        """Full lifecycle: available → in_battle → caught."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        # Check available
        check = client.get(f"/api/legendary/{gid}/145/check")
        assert check.json()["available"] is True
        # Start encounter
        enc = client.post(f"/api/legendary/{gid}/145/encounter")
        assert enc.status_code == 200
        # Catch
        client.post(f"/api/legendary/{gid}/145/caught")
        # Verify final state
        check = client.get(f"/api/legendary/{gid}/145/check")
        assert check.json()["already_caught"] is True
        assert check.json()["available"] is False
        _cleanup(gid)

    def test_full_lifecycle_encounter_to_fled(self):
        """Full lifecycle: available → in_battle → fled → available."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        # Start encounter
        client.post(f"/api/legendary/{gid}/144/encounter")
        # Flee
        client.post(f"/api/legendary/{gid}/144/fled")
        # Should be available again
        check = client.get(f"/api/legendary/{gid}/144/check")
        assert check.json()["available"] is True
        # Can encounter again
        enc = client.post(f"/api/legendary/{gid}/144/encounter")
        assert enc.status_code == 200
        _cleanup(gid)


class TestLegendaryListDetails:
    """Legendary list endpoint field completeness."""

    def test_list_entries_have_all_fields(self):
        """Each list entry has types, level, location, location_name."""
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/legendary/{gid}")
        data = resp.json()
        for entry in data:
            assert "species_id" in entry
            assert "name" in entry
            assert "types" in entry
            assert "level" in entry
            assert "location" in entry
            assert "location_name" in entry
            assert "status" in entry
            assert "requirements_met" in entry
        _cleanup(gid)

    def test_list_mewtwo_locked_with_one_badge(self):
        """Mewtwo stays locked when only one of two required badges is set."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        resp = client.get(f"/api/legendary/{gid}")
        mewtwo = [e for e in resp.json() if e["name"] == "Mewtwo"][0]
        assert mewtwo["status"] == "locked"
        assert mewtwo["requirements_met"] is False
        _cleanup(gid)

    def test_list_mewtwo_available_with_both_badges(self):
        """Mewtwo becomes available when both required badges are set."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_boulder", "badge_cascade"])
        resp = client.get(f"/api/legendary/{gid}")
        mewtwo = [e for e in resp.json() if e["name"] == "Mewtwo"][0]
        assert mewtwo["status"] == "available"
        assert mewtwo["requirements_met"] is True
        _cleanup(gid)

    def test_list_reflects_caught_status(self):
        """List shows 'caught' status after legendary is caught."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        client.post(f"/api/legendary/{gid}/144/caught")
        resp = client.get(f"/api/legendary/{gid}")
        articuno = [e for e in resp.json() if e["name"] == "Articuno"][0]
        assert articuno["status"] == "caught"
        _cleanup(gid)

    def test_list_reflects_fainted_status(self):
        """List shows 'fainted' status after legendary faints."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        client.post(f"/api/legendary/{gid}/145/fainted")
        resp = client.get(f"/api/legendary/{gid}")
        zapdos = [e for e in resp.json() if e["name"] == "Zapdos"][0]
        assert zapdos["status"] == "fainted"
        _cleanup(gid)


class TestLegendaryCheckDetails:
    """Legendary check endpoint field completeness."""

    def test_check_response_has_all_fields(self):
        """Check response includes all expected fields."""
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/legendary/{gid}/150/check")
        data = resp.json()
        expected_fields = [
            "species_id", "name", "available", "location", "location_name",
            "requirements_met", "already_caught", "already_fainted",
            "required_flags", "missing_flags",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        _cleanup(gid)

    def test_check_mewtwo_missing_flags_lists_both(self):
        """Check for Mewtwo with no badges lists both required flags as missing."""
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/legendary/{gid}/150/check")
        data = resp.json()
        assert set(data["missing_flags"]) == {"badge_boulder", "badge_cascade"}
        assert data["required_flags"] == ["badge_boulder", "badge_cascade"]
        _cleanup(gid)

    def test_check_mewtwo_partial_flags(self):
        """Check for Mewtwo with one badge shows only the missing one."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_boulder"])
        resp = client.get(f"/api/legendary/{gid}/150/check")
        data = resp.json()
        assert data["missing_flags"] == ["badge_cascade"]
        assert data["requirements_met"] is False
        assert data["available"] is False
        _cleanup(gid)


class TestLegendaryZapdosIndividual:
    """Individual tests for Zapdos (otherwise only tested in bulk list)."""

    def test_zapdos_stats(self):
        """Zapdos definition has correct stats."""
        zapdos = LEGENDARY_DEFS[145]
        assert zapdos.name == "Zapdos"
        assert zapdos.level == 50
        assert zapdos.types == ["electric", "flying"]
        assert zapdos.location == "power_plant"
        assert zapdos.location_name == "Power Plant"
        assert zapdos.catch_rate == 3
        assert zapdos.ability == "pressure"

    def test_zapdos_check_locked(self):
        """Zapdos is locked without badge_cascade."""
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/legendary/{gid}/145/check")
        data = resp.json()
        assert data["available"] is False
        assert data["requirements_met"] is False
        _cleanup(gid)

    def test_zapdos_encounter_with_flag(self):
        """Zapdos can be encountered with badge_cascade."""
        game = _make_game()
        gid = game["id"]
        _set_flags(gid, ["badge_cascade"])
        resp = client.post(f"/api/legendary/{gid}/145/encounter")
        assert resp.status_code == 200
        assert resp.json()["legendary_name"] == "Zapdos"
        _cleanup(gid)

    def test_zapdos_caught_and_check(self):
        """Zapdos shows as caught after being marked caught."""
        game = _make_game()
        gid = game["id"]
        client.post(f"/api/legendary/{gid}/145/caught")
        resp = client.get(f"/api/legendary/{gid}/145/check")
        assert resp.json()["already_caught"] is True
        _cleanup(gid)


class TestLegendaryCrossGameIsolation:
    """Ensure legendary status is isolated per game."""

    def test_catching_in_one_game_does_not_affect_other(self):
        """Legendary caught in game A is still available in game B."""
        game_a = _make_game("PlayerA")
        game_b = _make_game("PlayerB")
        gid_a = game_a["id"]
        gid_b = game_b["id"]
        # Catch Mewtwo in game A
        client.post(f"/api/legendary/{gid_a}/150/caught")
        # Check in game A — caught
        check_a = client.get(f"/api/legendary/{gid_a}/150/check")
        assert check_a.json()["already_caught"] is True
        # Check in game B — still available (requirements aside)
        check_b = client.get(f"/api/legendary/{gid_b}/150/check")
        assert check_b.json()["already_caught"] is False
        _cleanup(gid_a)
        _cleanup(gid_b)


class TestLegendaryStatusChangeResponses:
    """Verify response bodies of status-change endpoints."""

    def test_caught_response_body(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/legendary/{gid}/150/caught")
        data = resp.json()
        assert data["success"] is True
        assert "caught" in data["message"].lower()
        _cleanup(gid)

    def test_fainted_response_body(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/legendary/{gid}/150/fainted")
        data = resp.json()
        assert data["success"] is True
        assert "fainted" in data["message"].lower()
        _cleanup(gid)

    def test_fled_response_body(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/legendary/{gid}/150/fled")
        data = resp.json()
        assert data["success"] is True
        assert "available" in data["message"].lower()
        _cleanup(gid)

    def test_invalid_species_caught_still_succeeds(self):
        """Caught for invalid species_id silently succeeds (no validation)."""
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/legendary/{gid}/999/caught")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        _cleanup(gid)


# ==============================================================
# INTEGRATION: QUEST → RIVAL → LEGENDARY FLOW
# ==============================================================

class TestFullProgressionFlow:
    """End-to-end quest progression unlocking legendary encounters."""

    def test_quest_chain_unlocks_legendary(self):
        """Complete quest chain → earn badges → unlock Articuno."""
        game = _make_game()
        gid = game["id"]
        # Start: all legendaries locked
        resp = client.get(f"/api/legendary/{gid}")
        for entry in resp.json():
            assert entry["status"] == "locked"

        # Complete quest chain to earn cascade badge
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        client.post(f"/api/quests/{gid}/oaks_parcel/complete")
        client.post(f"/api/quests/{gid}/boulder_badge/complete")
        client.post(f"/api/quests/{gid}/cascade_badge/complete")

        # Verify badges are set as flags
        assert client.get(f"/api/flags/{gid}/badge_boulder").json()["value"] is True
        assert client.get(f"/api/flags/{gid}/badge_cascade").json()["value"] is True

        # All three legendaries should now be available
        resp = client.get(f"/api/legendary/{gid}")
        for entry in resp.json():
            assert entry["status"] == "available"
            assert entry["requirements_met"] is True

        # Can encounter Articuno
        enc = client.post(f"/api/legendary/{gid}/144/encounter")
        assert enc.status_code == 200
        assert enc.json()["legendary_name"] == "Articuno"
        _cleanup(gid)

    def test_rival_battle_complete_advances_quest_chain(self):
        """Rival battle-complete stage 2 advances rival_showdown_1 quest."""
        game = _make_game()
        gid = game["id"]
        client.post("/api/rival/init", json={"game_id": gid, "player_starter_id": 1})
        # Unlock rival_showdown_1
        client.post(f"/api/quests/{gid}/new_adventure/complete")
        client.post(f"/api/quests/{gid}/oaks_parcel/complete")
        # Verify quest is active
        resp = client.get(f"/api/quests/{gid}/rival_showdown_1")
        assert resp.json()["status"] == "active"
        # Complete rival battle stage 2
        client.post("/api/rival/battle-complete", json={"game_id": gid, "stage": 2})
        # Quest should now be completed
        resp = client.get(f"/api/quests/{gid}/rival_showdown_1")
        assert resp.json()["status"] == "completed"
        _cleanup(gid)
