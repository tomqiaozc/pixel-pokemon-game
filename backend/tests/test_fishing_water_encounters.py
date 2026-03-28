"""Tests for Sprint 9: Fishing & Water Encounters System."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.encounter_service import (
    check_encounter,
    get_encounter_table,
    get_species,
    generate_wild_pokemon,
    get_move_data,
)

client = TestClient(app)


# ──── New Water Pokemon Species ────────────────────────────

class TestWaterSpecies:
    def test_magikarp_exists(self):
        species = get_species(129)
        assert species is not None
        assert species.name == "Magikarp"
        assert "water" in species.types

    def test_gyarados_exists(self):
        species = get_species(130)
        assert species is not None
        assert species.name == "Gyarados"
        assert "water" in species.types
        assert "flying" in species.types

    def test_tentacool_exists(self):
        species = get_species(72)
        assert species is not None
        assert species.name == "Tentacool"
        assert "water" in species.types

    def test_tentacruel_exists(self):
        species = get_species(73)
        assert species is not None
        assert species.name == "Tentacruel"
        assert "water" in species.types

    def test_goldeen_exists(self):
        species = get_species(118)
        assert species is not None
        assert species.name == "Goldeen"
        assert "water" in species.types

    def test_seaking_exists(self):
        species = get_species(119)
        assert species is not None
        assert species.name == "Seaking"
        assert "water" in species.types

    def test_poliwag_exists(self):
        species = get_species(60)
        assert species is not None
        assert species.name == "Poliwag"
        assert "water" in species.types

    def test_psyduck_exists(self):
        species = get_species(54)
        assert species is not None
        assert species.name == "Psyduck"
        assert "water" in species.types

    def test_horsea_exists(self):
        species = get_species(116)
        assert species is not None
        assert species.name == "Horsea"
        assert "water" in species.types

    def test_shellder_exists(self):
        species = get_species(90)
        assert species is not None
        assert species.name == "Shellder"
        assert "water" in species.types

    def test_magikarp_evolves_to_gyarados(self):
        species = get_species(129)
        assert species.evolution is not None
        assert species.evolution.to == 130
        assert species.evolution.level == 20

    def test_goldeen_evolves_to_seaking(self):
        species = get_species(118)
        assert species.evolution is not None
        assert species.evolution.to == 119

    def test_water_species_have_learnsets(self):
        for sid in [129, 130, 72, 73, 118, 119, 60, 54, 116, 90]:
            species = get_species(sid)
            assert len(species.learnset) >= 2, f"{species.name} needs at least 2 learnset entries"

    def test_water_species_have_abilities(self):
        for sid in [129, 130, 72, 73, 118, 119, 60, 54, 116, 90]:
            species = get_species(sid)
            assert len(species.abilities) >= 1, f"{species.name} needs at least 1 ability"

    def test_generate_magikarp(self):
        pokemon = generate_wild_pokemon(129, 10)
        assert pokemon.name == "Magikarp"
        assert pokemon.level == 10
        assert len(pokemon.moves) >= 1


# ──── New Moves (Surf, Waterfall) ──────────────────────────

class TestNewWaterMoves:
    def test_surf_exists(self):
        move = get_move_data("Surf")
        assert move is not None
        assert move["type"] == "water"
        assert move["category"] == "special"
        assert move["power"] == 90
        assert move["accuracy"] == 100

    def test_waterfall_exists(self):
        move = get_move_data("Waterfall")
        assert move is not None
        assert move["type"] == "water"
        assert move["category"] == "physical"
        assert move["power"] == 80
        assert move["accuracy"] == 100


# ──── Fishing Rod Items ────────────────────────────────────

class TestFishingRodItems:
    def test_old_rod_in_items(self):
        resp = client.get("/api/inventory/items")
        if resp.status_code == 200:
            items = resp.json()
        else:
            from backend.services.item_service import get_all_items
            items = [i.model_dump() for i in get_all_items()]
        old_rod = next((i for i in items if i["name"] == "Old Rod"), None)
        assert old_rod is not None
        assert old_rod["category"] == "key_item"

    def test_good_rod_in_items(self):
        from backend.services.item_service import get_all_items
        items = [i.model_dump() for i in get_all_items()]
        good_rod = next((i for i in items if i["name"] == "Good Rod"), None)
        assert good_rod is not None
        assert good_rod["category"] == "key_item"

    def test_super_rod_in_items(self):
        from backend.services.item_service import get_all_items
        items = [i.model_dump() for i in get_all_items()]
        super_rod = next((i for i in items if i["name"] == "Super Rod"), None)
        assert super_rod is not None
        assert super_rod["category"] == "key_item"


# ──── Water Encounter Tables ──────────────────────────────

class TestWaterEncounterTables:
    def test_pallet_town_fishing_old_rod_table(self):
        table = get_encounter_table("pallet_town_fishing_old")
        assert table is not None
        assert table.encounter_type == "fishing"
        assert len(table.encounters) >= 1
        # Old Rod should mainly have Magikarp
        species_ids = [e.species_id for e in table.encounters]
        assert 129 in species_ids  # Magikarp

    def test_pallet_town_fishing_good_rod_table(self):
        table = get_encounter_table("pallet_town_fishing_good")
        assert table is not None
        assert table.encounter_type == "fishing"
        assert len(table.encounters) >= 2

    def test_pallet_town_fishing_super_rod_table(self):
        table = get_encounter_table("pallet_town_fishing_super")
        assert table is not None
        assert table.encounter_type == "fishing"
        assert len(table.encounters) >= 3

    def test_pallet_town_surfing_table(self):
        table = get_encounter_table("pallet_town_surfing")
        assert table is not None
        assert table.encounter_type == "water"
        assert len(table.encounters) >= 2

    def test_route_2_fishing_old_rod_table(self):
        table = get_encounter_table("route_2_fishing_old")
        assert table is not None
        assert table.encounter_type == "fishing"

    def test_fishing_encounter_check(self):
        """Fishing should always encounter (100% rate)."""
        table = get_encounter_table("pallet_town_fishing_old")
        assert table.base_encounter_rate == 1.0

    def test_surfing_encounter_rate(self):
        table = get_encounter_table("pallet_town_surfing")
        assert 0.1 <= table.base_encounter_rate <= 0.5


# ──── Fishing API Endpoint ─────────────────────────────────

class TestFishingEndpoint:
    def test_fish_endpoint_exists(self):
        resp = client.post("/api/encounter/fish", json={
            "area_id": "pallet_town",
            "rod_tier": "old",
        })
        assert resp.status_code == 200

    def test_fish_returns_pokemon(self):
        resp = client.post("/api/encounter/fish", json={
            "area_id": "pallet_town",
            "rod_tier": "old",
        })
        data = resp.json()
        assert data["encountered"] is True
        assert data["pokemon"] is not None
        assert data["pokemon"]["name"] == "Magikarp"

    def test_fish_good_rod_higher_levels(self):
        resp = client.post("/api/encounter/fish", json={
            "area_id": "pallet_town",
            "rod_tier": "good",
        })
        data = resp.json()
        assert data["encountered"] is True
        assert data["pokemon"] is not None

    def test_fish_super_rod_varied_species(self):
        species_seen = set()
        for _ in range(50):
            resp = client.post("/api/encounter/fish", json={
                "area_id": "pallet_town",
                "rod_tier": "super",
            })
            data = resp.json()
            species_seen.add(data["pokemon"]["name"])
        # Super Rod should have at least 3 different species
        assert len(species_seen) >= 3

    def test_fish_invalid_area(self):
        resp = client.post("/api/encounter/fish", json={
            "area_id": "nonexistent_area",
            "rod_tier": "old",
        })
        assert resp.status_code == 404

    def test_fish_invalid_rod(self):
        resp = client.post("/api/encounter/fish", json={
            "area_id": "pallet_town",
            "rod_tier": "mega",
        })
        assert resp.status_code == 400


# ──── Water Encounter Zones in Map Data ────────────────────

class TestWaterEncounterZones:
    def test_pallet_town_has_water_zone(self):
        resp = client.get("/api/maps/pallet_town")
        assert resp.status_code == 200
        data = resp.json()
        map_data = data.get("map", data)
        zones = map_data.get("encounter_zones", [])
        water_zones = [z for z in zones if "surfing" in z.get("encounter_table_id", "")
                       or "fishing" in z.get("encounter_table_id", "")]
        assert len(water_zones) >= 1
