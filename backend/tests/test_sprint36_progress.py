"""Tests for Sprint 36: PC storage, badge effects, rival system.

These tests verify PC box system, badge unlock effects,
and rival team progression data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── PC Storage ───────────────────────────────────────────────

class TestPCStorage:
    def test_file_exists(self):
        pc = _load_json("pc_storage.json")
        assert "total_boxes" in pc

    def test_box_count(self):
        pc = _load_json("pc_storage.json")
        assert pc["total_boxes"] == 12

    def test_pokemon_per_box(self):
        pc = _load_json("pc_storage.json")
        assert pc["pokemon_per_box"] == 30

    def test_total_capacity(self):
        pc = _load_json("pc_storage.json")
        assert pc["total_capacity"] == 360
        assert pc["total_capacity"] == pc["total_boxes"] * pc["pokemon_per_box"]

    def test_default_box_names(self):
        pc = _load_json("pc_storage.json")
        assert len(pc["default_box_names"]) == 12

    def test_features(self):
        pc = _load_json("pc_storage.json")
        features = pc["features"]
        assert features["rename_boxes"] is True
        assert features["move_pokemon"] is True
        assert features["release_pokemon"] is True

    def test_auto_switch(self):
        pc = _load_json("pc_storage.json")
        assert pc["auto_switch"]["enabled"] is True

    def test_access_locations(self):
        pc = _load_json("pc_storage.json")
        assert "pokemon_center" in pc["access_locations"]


# ──── Badge Effects ────────────────────────────────────────────

class TestBadgeEffects:
    def test_badge_count(self):
        badges = _load_json("badge_effects.json")
        assert len(badges) == 8

    EXPECTED_BADGES = [
        "boulder_badge", "cascade_badge", "thunder_badge", "rainbow_badge",
        "soul_badge", "marsh_badge", "volcano_badge", "earth_badge"
    ]

    @pytest.mark.parametrize("badge_id", EXPECTED_BADGES)
    def test_badge_exists(self, badge_id):
        badges = _load_json("badge_effects.json")
        assert badge_id in badges
        b = badges[badge_id]
        assert "name" in b
        assert "gym_leader" in b
        assert "location" in b
        assert "effects" in b

    def test_badge_numbers_sequential(self):
        badges = _load_json("badge_effects.json")
        numbers = sorted(b["badge_number"] for b in badges.values())
        assert numbers == list(range(1, 9))

    def test_earth_badge_unlocks_league(self):
        badges = _load_json("badge_effects.json")
        earth = badges["earth_badge"]
        assert earth["effects"].get("unlocks_pokemon_league") is True
        assert earth["effects"]["obedience_level"] == 255

    def test_cascade_badge_unlocks_cut(self):
        badges = _load_json("badge_effects.json")
        cascade = badges["cascade_badge"]
        assert cascade["effects"]["hm_move"] == "Cut"

    def test_soul_badge_unlocks_surf(self):
        badges = _load_json("badge_effects.json")
        soul = badges["soul_badge"]
        assert soul["effects"]["hm_move"] == "Surf"

    GYM_LEADERS = [
        ("boulder_badge", "Brock"), ("cascade_badge", "Misty"),
        ("thunder_badge", "Lt. Surge"), ("rainbow_badge", "Erika"),
        ("soul_badge", "Koga"), ("marsh_badge", "Sabrina"),
        ("volcano_badge", "Blaine"), ("earth_badge", "Giovanni"),
    ]

    @pytest.mark.parametrize("badge_id,leader", GYM_LEADERS)
    def test_gym_leaders(self, badge_id, leader):
        badges = _load_json("badge_effects.json")
        assert badges[badge_id]["gym_leader"] == leader


# ──── Rival System ─────────────────────────────────────────────

class TestRivalSystem:
    def test_encounter_count(self):
        rival = _load_json("rival_teams.json")
        assert len(rival) == 8

    def test_team_size_progression(self):
        rival = _load_json("rival_teams.json")
        encounters = sorted(rival.values(), key=lambda e: e.get("required_badges", 0))
        for i in range(len(encounters) - 1):
            assert len(encounters[i]["team"]) <= len(encounters[i+1]["team"])

    def test_level_progression(self):
        rival = _load_json("rival_teams.json")
        first = rival["rival_1_oak_lab"]
        last = rival["rival_8_champion"]
        max_first = max(p["level"] for p in first["team"])
        max_last = max(p["level"] for p in last["team"])
        assert max_last > max_first

    def test_champion_full_team(self):
        rival = _load_json("rival_teams.json")
        champ = rival["rival_8_champion"]
        assert len(champ["team"]) == 6
        assert champ["required_badges"] == 8

    def test_starter_evolves(self):
        rival = _load_json("rival_teams.json")
        assert rival["rival_1_oak_lab"]["team"][0]["species"] == "Squirtle"
        assert rival["rival_3_cerulean"]["team"][-1]["species"] == "Wartortle"
        assert rival["rival_8_champion"]["team"][-1]["species"] == "Blastoise"

    def test_all_have_required_fields(self):
        rival = _load_json("rival_teams.json")
        for eid, encounter in rival.items():
            assert "encounter_name" in encounter
            assert "location" in encounter
            assert "team" in encounter
            for pokemon in encounter["team"]:
                assert "species" in pokemon
                assert "level" in pokemon
                assert "moves" in pokemon

    def test_champion_blastoise_highest_level(self):
        rival = _load_json("rival_teams.json")
        champ = rival["rival_8_champion"]
        blastoise = next(p for p in champ["team"] if p["species"] == "Blastoise")
        assert blastoise["level"] == 63
        for p in champ["team"]:
            assert p["level"] <= blastoise["level"]


# ──── Counts ───────────────────────────────────────────────────

class TestCounts:
    def test_items_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 93

    def test_moves_unchanged(self):
        moves = _load_json("moves.json")
        assert len(moves) == 174

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151

    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132
