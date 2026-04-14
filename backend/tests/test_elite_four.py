"""Tests for Sprint 21: Elite Four & Champion.

These tests verify Elite Four maps, NPCs, dialogues, new species,
and the Elite Four service state machine.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Elite Four Maps ──────────────────────────────────────

class TestEliteFourMaps:
    """All 7 new maps must exist in maps.json."""

    EXPECTED_MAPS = [
        "elite_four_lobby",
        "lorelei_room",
        "bruno_room",
        "agatha_room",
        "lance_room",
        "champion_room",
        "hall_of_fame",
    ]

    @pytest.mark.parametrize("map_id", EXPECTED_MAPS)
    def test_map_exists(self, map_id):
        maps = _load_json("maps.json")
        found = next((m for m in maps if m["id"] == map_id), None)
        assert found is not None, f"Map {map_id} not found in maps.json"

    def test_total_maps_count(self):
        maps = _load_json("maps.json")
        assert len(maps) == 112


# ──── New Pokemon Species ────────────────────────────────────

class TestEliteFourSpecies:
    EXPECTED_SPECIES = [
        (87, "Dewgong"),
        (91, "Cloyster"),
        (131, "Lapras"),
        (148, "Dragonair"),
        (149, "Dragonite"),
    ]

    @pytest.mark.parametrize("species_id,name", EXPECTED_SPECIES)
    def test_species_exists(self, species_id, name):
        species_data = _load_json("pokemon_species.json")
        species = next((s for s in species_data if s.get("id") == species_id), None)
        assert species is not None, f"Species {name} (ID {species_id}) not found"
        assert species["name"] == name

    def test_all_species_have_stats(self):
        species_data = _load_json("pokemon_species.json")
        for sid, name in self.EXPECTED_SPECIES:
            species = next((s for s in species_data if s.get("id") == sid), None)
            assert species is not None, f"Species {name} (ID {sid}) not found"
            stats = species.get("stats", {})
            for stat in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
                assert stat in stats, f"Species {name} (ID {sid}) missing stat {stat}"

    def test_total_species_count(self):
        species_data = _load_json("pokemon_species.json")
        assert len(species_data) == 105


# ──── NPCs ───────────────────────────────────────────────────

class TestEliteFourNPCs:
    EXPECTED_NPCS = [
        "elite_four_guide",
        "lorelei_npc",
        "bruno_npc",
        "agatha_npc",
        "lance_npc",
        "champion_rival_npc",
        "prof_oak_hof",
    ]

    @pytest.mark.parametrize("npc_id", EXPECTED_NPCS)
    def test_npc_exists(self, npc_id):
        npcs = _load_json("npcs.json")
        found = next((n for n in npcs if n["id"] == npc_id), None)
        assert found is not None, f"NPC {npc_id} not found in npcs.json"

    def test_total_npc_count(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 91


# ──── Dialogues ──────────────────────────────────────────────

class TestEliteFourDialogues:
    EXPECTED_DIALOGUES = [
        "elite_four_guide_dialogue",
        "lorelei_dialogue",
        "bruno_dialogue",
        "agatha_dialogue",
        "lance_dialogue",
        "champion_dialogue",
        "prof_oak_hof_dialogue",
    ]

    @pytest.mark.parametrize("dialogue_id", EXPECTED_DIALOGUES)
    def test_dialogue_exists(self, dialogue_id):
        dialogues = _load_json("dialogues.json")
        assert dialogue_id in dialogues, f"Dialogue {dialogue_id} not found"
        assert len(dialogues[dialogue_id].get("nodes", [])) >= 1

    def test_total_dialogue_count(self):
        dialogues = _load_json("dialogues.json")
        assert len(dialogues) == 69


# ──── Trainers ───────────────────────────────────────────────

class TestEliteFourTrainers:
    def test_total_trainer_count(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 94

    def test_all_trainers_have_teams(self):
        trainers = _load_json("trainers.json")
        for trainer in trainers:
            assert len(trainer.get("pokemon_team", [])) >= 1, (
                f"Trainer {trainer.get('id')} has no pokemon team"
            )


# ──── Elite Four Service ─────────────────────────────────────

class TestEliteFourService:
    def test_import_service(self):
        from backend.services.elite_four_service import (
            EliteFourState,
            get_elite_four_state,
            enter_elite_four,
            defeat_member,
            enter_hall_of_fame,
            get_hall_of_fame,
            reset_elite_four,
        )

    def test_state_enum(self):
        from backend.services.elite_four_service import EliteFourState
        assert EliteFourState.NOT_ENTERED == "not_entered"
        assert EliteFourState.HALL_OF_FAME == "hall_of_fame"

    def test_elite_four_members(self):
        from backend.services.elite_four_service import ELITE_FOUR_MEMBERS
        assert "lorelei" in ELITE_FOUR_MEMBERS
        assert "bruno" in ELITE_FOUR_MEMBERS
        assert "agatha" in ELITE_FOUR_MEMBERS
        assert "lance" in ELITE_FOUR_MEMBERS

    def test_champion_data(self):
        from backend.services.elite_four_service import CHAMPION_DATA
        assert CHAMPION_DATA["name"] == "Champion"
        assert len(CHAMPION_DATA["pokemon_team"]) == 6

    def test_member_teams(self):
        from backend.services.elite_four_service import ELITE_FOUR_MEMBERS
        for name, member in ELITE_FOUR_MEMBERS.items():
            assert len(member["pokemon_team"]) == 5, f"{name} should have 5 Pokemon"

    def test_get_member_data(self):
        from backend.services.elite_four_service import get_member_data
        lorelei = get_member_data("lorelei")
        assert lorelei is not None
        assert lorelei["name"] == "Lorelei"
        assert lorelei["specialty"] == "ice"

        champion = get_member_data("champion")
        assert champion is not None
        assert champion["name"] == "Champion"

        unknown = get_member_data("unknown")
        assert unknown is None


# ──── Quest Definitions ──────────────────────────────────────

class TestEliteFourQuests:
    def test_elite_four_quest_defined(self):
        from backend.services.quest_service import _QUEST_DEFS
        quest = next((q for q in _QUEST_DEFS if q["id"] == "elite_four"), None)
        assert quest is not None
        assert quest["type"] == "main"
        assert len(quest["objectives"]) == 4

    def test_champion_quest_defined(self):
        from backend.services.quest_service import _QUEST_DEFS
        quest = next((q for q in _QUEST_DEFS if q["id"] == "champion"), None)
        assert quest is not None
        assert quest["type"] == "main"
        assert quest["prerequisite_quests"] == ["elite_four"]


# ──── Gym Count Unchanged ────────────────────────────────────

class TestGymCountUnchanged:
    def test_still_eight_gyms(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 8
