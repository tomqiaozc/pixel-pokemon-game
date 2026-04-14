"""Tests for Sprint 30: Complete Gen 1 moves, town NPC dialogues, townsfolk NPCs.

These tests verify the move database expansion to 174 (full Gen 1),
18 new town dialogues, and 9 new townsfolk NPCs.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Move Database ────────────────────────────────────────────

class TestMoveDatabase:
    def test_move_count(self):
        moves = _load_json("moves.json")
        assert len(moves) == 174

    SPRINT_30_NEW_MOVES = [
        "Tri Attack", "Mega Drain", "Acid Armor", "Bubble",
        "Double Edge", "Double Slap", "Dragon Rage", "Focus Energy",
        "Fury Attack", "Growth", "Guillotine", "Haze",
        "Jump Kick", "Light Screen", "Minimize", "Peck",
        "Poison Gas", "Poison Powder", "Psybeam", "Roar",
        "Self Destruct", "Sludge", "Smokescreen", "Soft Boiled",
        "Sonic Boom", "Spore", "Supersonic", "Thrash",
        "Twineedle", "Vice Grip", "Whirlwind",
    ]

    @pytest.mark.parametrize("move_name", SPRINT_30_NEW_MOVES)
    def test_new_move_exists(self, move_name):
        moves = _load_json("moves.json")
        assert move_name in moves, f"Move {move_name} not found"
        move = moves[move_name]
        assert "name" in move
        assert "type" in move
        assert "category" in move
        assert "pp" in move

    def test_all_moves_have_required_fields(self):
        moves = _load_json("moves.json")
        required = {"name", "type", "category", "power", "accuracy", "pp"}
        for move_name, move in moves.items():
            for field in required:
                assert field in move, f"{move_name} missing {field}"

    def test_status_moves_have_zero_power(self):
        moves = _load_json("moves.json")
        for name, move in moves.items():
            if move["category"] == "status":
                assert move["power"] == 0, f"{name} is status but power={move['power']}"

    EXPECTED_TYPES = [
        "normal", "fire", "water", "electric", "grass", "ice",
        "fighting", "poison", "ground", "flying", "psychic",
        "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy"
    ]

    def test_all_move_types_valid(self):
        moves = _load_json("moves.json")
        for name, move in moves.items():
            assert move["type"] in self.EXPECTED_TYPES, (
                f"{name} has invalid type: {move['type']}"
            )

    def test_all_categories_valid(self):
        moves = _load_json("moves.json")
        valid_cats = {"physical", "special", "status"}
        for name, move in moves.items():
            assert move["category"] in valid_cats, (
                f"{name} has invalid category: {move['category']}"
            )

    def test_dragon_rage_is_dragon_type(self):
        moves = _load_json("moves.json")
        assert moves["Dragon Rage"]["type"] == "dragon"

    def test_spore_is_grass_type(self):
        moves = _load_json("moves.json")
        assert moves["Spore"]["type"] == "grass"
        assert moves["Spore"]["accuracy"] == 100

    def test_self_destruct_high_power(self):
        moves = _load_json("moves.json")
        assert moves["Self Destruct"]["power"] == 200

    def test_guillotine_is_ohko(self):
        moves = _load_json("moves.json")
        assert moves["Guillotine"]["accuracy"] == 30


# ──── Town NPC Dialogues ───────────────────────────────────────

class TestTownDialogues:
    def test_dialogue_count(self):
        dialogues = _load_json("dialogues.json")
        assert len(dialogues) == 90

    SPRINT_30_DIALOGUES = [
        "pallet_townsfolk_1", "pallet_townsfolk_2",
        "viridian_townsfolk_1", "viridian_townsfolk_2",
        "pewter_townsfolk_1", "pewter_townsfolk_2",
        "cerulean_townsfolk_1", "cerulean_townsfolk_2",
        "vermilion_townsfolk_1", "vermilion_townsfolk_2",
        "celadon_townsfolk_1", "celadon_townsfolk_2",
        "lavender_townsfolk_1", "saffron_townsfolk_1",
        "fuchsia_townsfolk_1", "cinnabar_townsfolk_1",
        "cinnabar_townsfolk_2", "indigo_plateau_guard",
    ]

    @pytest.mark.parametrize("dialogue_id", SPRINT_30_DIALOGUES)
    def test_dialogue_exists(self, dialogue_id):
        dialogues = _load_json("dialogues.json")
        assert dialogue_id in dialogues, f"Dialogue {dialogue_id} not found"
        assert "nodes" in dialogues[dialogue_id]
        assert len(dialogues[dialogue_id]["nodes"]) > 0

    def test_sprint30_dialogues_have_start_node(self):
        dialogues = _load_json("dialogues.json")
        for did in self.SPRINT_30_DIALOGUES:
            nodes = dialogues[did]["nodes"]
            node_ids = [n["id"] for n in nodes]
            assert "start" in node_ids, f"Dialogue {did} missing start node"

    def test_all_nodes_have_text(self):
        dialogues = _load_json("dialogues.json")
        for did, dialogue in dialogues.items():
            for node in dialogue["nodes"]:
                assert "text" in node, f"Dialogue {did} node {node.get('id')} missing text"
                assert len(node["text"]) > 0

    def test_multi_node_dialogues(self):
        dialogues = _load_json("dialogues.json")
        multi_node = [
            "viridian_townsfolk_1", "pewter_townsfolk_1",
            "cerulean_townsfolk_2", "vermilion_townsfolk_2",
            "celadon_townsfolk_1", "lavender_townsfolk_1",
            "saffron_townsfolk_1", "fuchsia_townsfolk_1",
            "cinnabar_townsfolk_1", "indigo_plateau_guard",
        ]
        for did in multi_node:
            assert len(dialogues[did]["nodes"]) >= 2, f"{did} should have 2+ nodes"


# ──── Townsfolk NPCs ──────────────────────────────────────────

class TestTownsfolkNPCs:
    def test_npc_count(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 103

    def test_townsfolk_npcs_exist(self):
        npcs = _load_json("npcs.json")
        npc_ids = {n["id"] for n in npcs}
        expected_townsfolk = [
            "pallet_townsfolk_1", "pallet_townsfolk_2",
            "viridian_townsfolk_1", "viridian_townsfolk_2",
            "pewter_townsfolk_1", "pewter_townsfolk_2",
            "cerulean_townsfolk_1", "cerulean_townsfolk_2",
            "vermilion_townsfolk_1", "vermilion_townsfolk_2",
            "celadon_townsfolk_1", "celadon_townsfolk_2",
            "lavender_townsfolk_1", "saffron_townsfolk_1",
            "fuchsia_townsfolk_1", "cinnabar_townsfolk_1",
            "cinnabar_townsfolk_2", "indigo_plateau_guard",
        ]
        for npc_id in expected_townsfolk:
            assert npc_id in npc_ids, f"NPC {npc_id} not found"

    def test_all_npcs_have_required_fields(self):
        npcs = _load_json("npcs.json")
        for npc in npcs:
            assert "id" in npc
            assert "name" in npc
            assert "npc_type" in npc
            assert "facing" in npc
            assert "position" in npc

    def test_townsfolk_have_dialogue_refs(self):
        npcs = _load_json("npcs.json")
        dialogues = _load_json("dialogues.json")
        townsfolk = [n for n in npcs if n["npc_type"] == "townsfolk"]
        for npc in townsfolk:
            if "dialogue_tree_id" in npc:
                assert npc["dialogue_tree_id"] in dialogues, (
                    f"NPC {npc['id']} references missing dialogue {npc['dialogue_tree_id']}"
                )


# ──── Counts Unchanged ─────────────────────────────────────────

class TestCountsUnchanged:
    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151

    def test_items_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 75

    def test_trainers_unchanged(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 116

    def test_encounter_tables_unchanged(self):
        tables = _load_json("encounter_tables.json")
        assert len(tables) == 52

    def test_abilities_unchanged(self):
        abilities = _load_json("abilities.json")
        assert len(abilities) == 51

    def test_shops_unchanged(self):
        shops = _load_json("shops.json")
        assert len(shops) == 11
