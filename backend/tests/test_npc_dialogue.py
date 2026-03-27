"""Tests for NPC and dialogue system."""
import pytest

from backend.services.npc_service import (
    get_npcs_by_map,
    get_npc,
    get_dialogue_tree,
    get_dialogue_node,
    process_dialogue_choice,
)


class TestNPCData:
    def test_pallet_town_npcs(self):
        npcs = get_npcs_by_map("pallet_town")
        assert len(npcs) >= 4  # Prof Oak, Mom, Blue, Bug Catcher, Lass
        names = {n.name for n in npcs}
        assert "Professor Oak" in names
        assert "Mom" in names
        assert "Blue" in names

    def test_pokemon_center_npcs(self):
        npcs = get_npcs_by_map("pokemon_center")
        assert len(npcs) >= 1
        names = {n.name for n in npcs}
        assert "Nurse Joy" in names

    def test_npc_by_id(self):
        npc = get_npc("prof_oak")
        assert npc is not None
        assert npc.name == "Professor Oak"
        assert npc.npc_type == "professor"

    def test_npc_not_found(self):
        npc = get_npc("nonexistent")
        assert npc is None

    def test_npc_positions(self):
        npc = get_npc("prof_oak")
        assert "x" in npc.position
        assert "y" in npc.position

    def test_npc_facing_directions(self):
        valid_dirs = {"up", "down", "left", "right"}
        for npc_id in ["prof_oak", "mom", "rival"]:
            npc = get_npc(npc_id)
            assert npc.facing in valid_dirs


class TestDialogueTrees:
    def test_prof_oak_dialogue(self):
        tree = get_dialogue_tree("prof_oak_intro")
        assert tree is not None
        assert len(tree.nodes) >= 6

    def test_dialogue_starts_at_start(self):
        tree = get_dialogue_tree("prof_oak_intro")
        start_node = get_dialogue_node(tree, "start")
        assert start_node is not None
        assert "Welcome" in start_node.text

    def test_mom_dialogue(self):
        tree = get_dialogue_tree("mom_dialogue")
        assert tree is not None
        start = get_dialogue_node(tree, "start")
        assert start is not None
        assert start.next is not None

    def test_rival_dialogue(self):
        tree = get_dialogue_tree("rival_intro")
        assert tree is not None

    def test_nurse_dialogue_has_choices(self):
        tree = get_dialogue_tree("nurse_dialogue")
        heal_prompt = get_dialogue_node(tree, "heal_prompt")
        assert heal_prompt is not None
        assert heal_prompt.choices is not None
        assert len(heal_prompt.choices) == 2

    def test_prof_oak_starter_choices(self):
        tree = get_dialogue_tree("prof_oak_intro")
        choose_node = get_dialogue_node(tree, "choose_starter")
        assert choose_node is not None
        assert choose_node.choices is not None
        assert len(choose_node.choices) == 3
        labels = [c.label for c in choose_node.choices]
        assert "Bulbasaur" in labels
        assert "Charmander" in labels
        assert "Squirtle" in labels


class TestDialogueProcessing:
    def test_advance_dialogue(self):
        next_node, effects = process_dialogue_choice("prof_oak", "start")
        assert next_node is not None
        assert next_node.id == "intro2"

    def test_dialogue_chain(self):
        # Follow the chain: start -> intro2 -> intro3
        node, _ = process_dialogue_choice("prof_oak", "start")
        assert node.id == "intro2"
        node, _ = process_dialogue_choice("prof_oak", "intro2")
        assert node.id == "intro3"

    def test_choose_starter_bulbasaur(self):
        node, effects = process_dialogue_choice("prof_oak", "choose_starter", 0)
        assert node is not None
        assert node.id == "chose_bulbasaur"
        assert "Bulbasaur" in node.text

    def test_choose_starter_charmander(self):
        node, effects = process_dialogue_choice("prof_oak", "choose_starter", 1)
        assert node.id == "chose_charmander"

    def test_choose_starter_squirtle(self):
        node, effects = process_dialogue_choice("prof_oak", "choose_starter", 2)
        assert node.id == "chose_squirtle"

    def test_heal_action(self):
        node, effects = process_dialogue_choice("nurse_joy", "heal_prompt", 0)
        assert node.id == "healing"
        # The healing node has a heal action
        assert any(e.get("type") == "heal" for e in effects)

    def test_decline_heal(self):
        node, effects = process_dialogue_choice("nurse_joy", "heal_prompt", 1)
        assert node.id == "goodbye"

    def test_dialogue_end(self):
        # Mom's last node has next=null
        node, effects = process_dialogue_choice("mom", "mom3")
        assert node is None

    def test_invalid_npc(self):
        node, effects = process_dialogue_choice("nonexistent", "start")
        assert node is None
        assert effects == []

    def test_invalid_node(self):
        node, effects = process_dialogue_choice("prof_oak", "nonexistent_node")
        assert node is None
        assert effects == []


class TestNPCAPI:
    def test_list_npcs_by_map(self, client):
        resp = client.get("/api/npcs/pallet_town")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 4
        assert any(n["name"] == "Professor Oak" for n in data)

    def test_list_npcs_empty_map(self, client):
        resp = client.get("/api/npcs/nonexistent_map")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_npc_dialogue(self, client):
        resp = client.get("/api/dialogue/prof_oak")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "prof_oak_intro"
        assert len(data["nodes"]) >= 6

    def test_get_dialogue_not_found(self, client):
        resp = client.get("/api/dialogue/nonexistent")
        assert resp.status_code == 404

    def test_dialogue_choice_endpoint(self, client):
        resp = client.post("/api/dialogue/choice", json={
            "npc_id": "prof_oak",
            "node_id": "start",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["node"]["id"] == "intro2"

    def test_dialogue_with_choice_index(self, client):
        resp = client.post("/api/dialogue/choice", json={
            "npc_id": "prof_oak",
            "node_id": "choose_starter",
            "choice_index": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["node"]["id"] == "chose_bulbasaur"


class TestChooseStarterAPI:
    """Test the new choose-starter endpoint."""

    def test_choose_bulbasaur(self, client):
        resp = client.post("/api/game/choose-starter", json={
            "player_name": "Ash",
            "starter_id": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["player"]["team"][0]["name"] == "Bulbasaur"

    def test_choose_charmander(self, client):
        resp = client.post("/api/game/choose-starter", json={
            "player_name": "Red",
            "starter_id": 4,
        })
        assert resp.status_code == 200
        assert resp.json()["player"]["team"][0]["name"] == "Charmander"

    def test_choose_squirtle(self, client):
        resp = client.post("/api/game/choose-starter", json={
            "player_name": "Blue",
            "starter_id": 7,
        })
        assert resp.status_code == 200

    def test_invalid_starter_id(self, client):
        resp = client.post("/api/game/choose-starter", json={
            "player_name": "Ash",
            "starter_id": 10,  # Pidgey is not a starter
        })
        assert resp.status_code == 400

    def test_save_game_validation_fixed(self, client):
        """Verify bug #23 fix: invalid player data returns 422 not 500."""
        game_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = game_resp.json()["id"]

        resp = client.post(f"/api/game/{game_id}/save", json={
            "player": {"invalid": "data"},
        })
        assert resp.status_code == 422
