"""Tests for Sprint 70: Poke Center locations, Fly destinations, evolution methods.

These tests verify Poke Center healing data, Fly destination configuration,
and complete Gen 1 evolution method data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Poke Center Locations ──────────────────────────────────

class TestPokeCenterLocations:
    def test_pokecenter_count(self):
        pc = _load_json("pokecenter_locations.json")
        assert len(pc["pokecenters"]) == 11

    def test_total_field_matches(self):
        pc = _load_json("pokecenter_locations.json")
        assert pc["total_centers"] == len(pc["pokecenters"])

    def test_pokecenters_have_fields(self):
        pc = _load_json("pokecenter_locations.json")
        for center in pc["pokecenters"]:
            assert "id" in center
            assert "city" in center
            assert "map_id" in center
            assert "services" in center
            assert "nurse_name" in center

    def test_unique_pokecenter_ids(self):
        pc = _load_json("pokecenter_locations.json")
        ids = [c["id"] for c in pc["pokecenters"]]
        assert len(ids) == len(set(ids))

    def test_all_have_heal_service(self):
        pc = _load_json("pokecenter_locations.json")
        for center in pc["pokecenters"]:
            assert "heal" in center["services"]

    def test_all_have_pc_storage(self):
        pc = _load_json("pokecenter_locations.json")
        for center in pc["pokecenters"]:
            assert "pc_storage" in center["services"]

    def test_heal_is_free(self):
        pc = _load_json("pokecenter_locations.json")
        assert pc["heal_config"]["heal_cost"] == 0

    def test_heal_restores_everything(self):
        pc = _load_json("pokecenter_locations.json")
        cfg = pc["heal_config"]
        assert cfg["cures_status"] is True
        assert cfg["restores_pp"] is True
        assert cfg["revives_fainted"] is True
        assert cfg["heal_all_party"] is True

    def test_sets_respawn_point(self):
        pc = _load_json("pokecenter_locations.json")
        assert pc["heal_config"]["sets_respawn_point"] is True

    def test_dialogue_entries(self):
        pc = _load_json("pokecenter_locations.json")
        d = pc["dialogue"]
        assert len(d) >= 4
        assert "greeting" in d
        assert "heal_prompt" in d
        assert "done" in d


# ──── Fly Destinations ───────────────────────────────────────

class TestFlyDestinations:
    def test_destination_count(self):
        fd = _load_json("fly_destinations.json")
        assert len(fd["destinations"]) == 11

    def test_total_field_matches(self):
        fd = _load_json("fly_destinations.json")
        assert fd["total_destinations"] == len(fd["destinations"])

    def test_destinations_have_fields(self):
        fd = _load_json("fly_destinations.json")
        for dest in fd["destinations"]:
            assert "id" in dest
            assert "name" in dest
            assert "map_id" in dest
            assert "landing_x" in dest
            assert "landing_y" in dest
            assert "unlock" in dest

    def test_unique_destination_ids(self):
        fd = _load_json("fly_destinations.json")
        ids = [d["id"] for d in fd["destinations"]]
        assert len(ids) == len(set(ids))

    def test_all_unlock_by_visit(self):
        fd = _load_json("fly_destinations.json")
        for dest in fd["destinations"]:
            assert dest["unlock"] == "visited"

    def test_badge_required(self):
        fd = _load_json("fly_destinations.json")
        assert fd["badge_required"] == "Thunder Badge"
        assert fd["badge_number"] == 3

    def test_fly_rules(self):
        fd = _load_json("fly_destinations.json")
        rules = fd["fly_rules"]
        assert rules["usable_outdoors_only"] is True
        assert rules["usable_in_caves"] is False
        assert rules["usable_in_buildings"] is False
        assert rules["requires_pokemon_with_fly"] is True

    def test_pallet_town_included(self):
        fd = _load_json("fly_destinations.json")
        names = [d["name"] for d in fd["destinations"]]
        assert "Pallet Town" in names

    def test_indigo_plateau_included(self):
        fd = _load_json("fly_destinations.json")
        names = [d["name"] for d in fd["destinations"]]
        assert "Indigo Plateau" in names


# ──── Evolution Methods ──────────────────────────────────────

class TestEvolutionMethods:
    def test_evolution_count(self):
        em = _load_json("evolution_methods.json")
        assert len(em["evolutions"]) == 72

    def test_total_field_matches(self):
        em = _load_json("evolution_methods.json")
        assert em["total_evolutions"] == len(em["evolutions"])

    def test_evolutions_have_fields(self):
        em = _load_json("evolution_methods.json")
        for evo in em["evolutions"]:
            assert "from" in evo
            assert "to" in evo
            assert "method" in evo

    def test_level_up_evolutions_have_level(self):
        em = _load_json("evolution_methods.json")
        level_ups = [e for e in em["evolutions"] if e["method"] == "level_up"]
        for evo in level_ups:
            assert "level" in evo
            assert evo["level"] > 0

    def test_stone_evolutions_have_stone(self):
        em = _load_json("evolution_methods.json")
        stones = [e for e in em["evolutions"] if e["method"] == "stone"]
        for evo in stones:
            assert "stone" in evo
            assert len(evo["stone"]) > 0

    def test_trade_evolutions(self):
        em = _load_json("evolution_methods.json")
        trades = [e for e in em["evolutions"] if e["method"] == "trade"]
        assert len(trades) == 4
        species = {t["from"] for t in trades}
        assert "Kadabra" in species
        assert "Machoke" in species
        assert "Graveler" in species
        assert "Haunter" in species

    def test_eevee_three_evolutions(self):
        em = _load_json("evolution_methods.json")
        eevee_evos = [e for e in em["evolutions"] if e["from"] == "Eevee"]
        assert len(eevee_evos) == 3
        targets = {e["to"] for e in eevee_evos}
        assert "Vaporeon" in targets
        assert "Jolteon" in targets
        assert "Flareon" in targets

    def test_five_evolution_stones(self):
        em = _load_json("evolution_methods.json")
        stones = em["method_types"]["stone"]["stones"]
        assert len(stones) == 5
        assert "Fire Stone" in stones
        assert "Moon Stone" in stones

    def test_cancel_rules(self):
        em = _load_json("evolution_methods.json")
        rules = em["evolution_rules"]
        assert rules["can_cancel"] is True
        assert rules["trade_evolution_no_cancel"] is True

    def test_valid_method_types(self):
        em = _load_json("evolution_methods.json")
        valid = {"level_up", "stone", "trade"}
        for evo in em["evolutions"]:
            assert evo["method"] in valid


# ──── Counts ──────────────────────────────────────────────────

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
