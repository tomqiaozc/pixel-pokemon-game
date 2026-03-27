"""Tests for encounter system and wild Pokemon generation."""
import pytest
from unittest.mock import patch

from backend.services.encounter_service import (
    check_encounter,
    generate_wild_pokemon,
    get_encounter_table,
    get_species,
    get_all_species,
    _calc_stat,
    _generate_moves_for_level,
)


class TestSpeciesData:
    def test_all_species_load(self):
        species = get_all_species()
        assert len(species) >= 16  # At least starters + evolutions + wild

    def test_starter_species_exist(self):
        for sid in [1, 4, 7]:
            s = get_species(sid)
            assert s is not None

    def test_wild_species_exist(self):
        for sid in [10, 13, 15]:  # Pidgey, Rattata, Pikachu
            s = get_species(sid)
            assert s is not None

    def test_species_have_learnsets(self):
        for s in get_all_species():
            assert len(s.learnset) > 0, f"{s.name} has no learnset"

    def test_species_have_valid_types(self):
        valid_types = {"grass", "poison", "fire", "water", "normal", "flying", "electric", "bug", "rock", "ground", "psychic"}
        for s in get_all_species():
            for t in s.types:
                assert t in valid_types, f"{s.name} has invalid type: {t}"

    def test_evolution_chains(self):
        # Bulbasaur -> Ivysaur -> Venusaur
        b = get_species(1)
        assert b.evolution is not None
        assert b.evolution.to == 2
        assert b.evolution.level == 16

        i = get_species(2)
        assert i.evolution is not None
        assert i.evolution.to == 3
        assert i.evolution.level == 32

        v = get_species(3)
        assert v.evolution is None  # Final form

    def test_pikachu_has_no_evolution_in_data(self):
        # Pikachu doesn't evolve via level in this game
        p = get_species(15)
        assert p.evolution is None


class TestEncounterTables:
    def test_route_1_exists(self):
        table = get_encounter_table("route_1")
        assert table is not None
        assert table.name == "Route 1"

    def test_route_1_encounter_rate(self):
        table = get_encounter_table("route_1")
        assert table.base_encounter_rate == 0.20

    def test_route_1_species(self):
        table = get_encounter_table("route_1")
        species_ids = {e.species_id for e in table.encounters}
        assert 10 in species_ids  # Pidgey
        assert 13 in species_ids  # Rattata

    def test_route_2_exists(self):
        table = get_encounter_table("route_2")
        assert table is not None

    def test_viridian_forest_higher_rate(self):
        table = get_encounter_table("viridian_forest")
        assert table.base_encounter_rate == 0.25

    def test_nonexistent_area(self):
        table = get_encounter_table("nonexistent")
        assert table is None

    def test_encounter_weights_positive(self):
        for area_id in ["route_1", "route_2", "viridian_forest"]:
            table = get_encounter_table(area_id)
            for entry in table.encounters:
                assert entry.weight > 0
                assert entry.min_level <= entry.max_level


class TestWildPokemonGeneration:
    def test_generate_pidgey(self):
        wild = generate_wild_pokemon(10, 5)
        assert wild.name == "Pidgey"
        assert wild.level == 5
        assert wild.current_hp > 0
        assert len(wild.moves) > 0

    def test_generate_at_different_levels(self):
        wild_3 = generate_wild_pokemon(10, 3)
        wild_10 = generate_wild_pokemon(10, 10)
        # Higher level should have higher HP
        assert wild_10.stats.hp >= wild_3.stats.hp

    def test_generated_pokemon_has_level_appropriate_moves(self):
        # Level 3 Pidgey should know Tackle (lv1) but not Gust (lv9)
        wild = generate_wild_pokemon(10, 3)
        move_names = [m.name for m in wild.moves]
        assert "Tackle" in move_names

    def test_max_4_moves(self):
        # Level 25 Pidgey would have more than 4 moves available
        wild = generate_wild_pokemon(10, 25)
        assert len(wild.moves) <= 4

    def test_invalid_species(self):
        with pytest.raises(ValueError):
            generate_wild_pokemon(999, 5)

    def test_stats_calculated_correctly(self):
        # HP formula: ((2 * base + iv) * level) / 100 + level + 10
        hp = _calc_stat(40, 5, 0, is_hp=True)
        expected = ((2 * 40 + 0) * 5) // 100 + 5 + 10
        assert hp == expected

    def test_catch_rate_set(self):
        wild = generate_wild_pokemon(10, 5)
        assert wild.catch_rate == 255  # Pidgey has 255 catch rate


class TestEncounterCheck:
    def test_no_encounter_in_unknown_area(self):
        result = check_encounter("no_such_area")
        assert result.encountered is False

    def test_encounter_can_happen(self):
        """With mocked random, ensure encounter triggers."""
        with patch("backend.services.encounter_service.random") as mock_random:
            mock_random.random.return_value = 0.1  # Below 0.20 rate
            # weight roll, level roll, then 6 IV rolls
            mock_random.randint.side_effect = [50, 4, 15, 15, 15, 15, 15, 15]

            result = check_encounter("route_1")
            assert result.encountered is True
            assert result.pokemon is not None
            assert result.pokemon.level >= 2

    def test_no_encounter_on_high_roll(self):
        """Encounter shouldn't trigger when random > encounter rate."""
        with patch("backend.services.encounter_service.random") as mock_random:
            mock_random.random.return_value = 0.99  # Above 0.20 rate

            result = check_encounter("route_1")
            assert result.encountered is False


class TestEncounterAPI:
    def test_starters_endpoint(self, client):
        resp = client.get("/api/encounter/starters")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        names = {s["name"] for s in data}
        assert names == {"Bulbasaur", "Charmander", "Squirtle"}

    def test_species_list(self, client):
        resp = client.get("/api/encounter/species")
        assert resp.status_code == 200
        assert len(resp.json()) >= 16

    def test_species_detail(self, client):
        resp = client.get("/api/encounter/species/15")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Pikachu"

    def test_species_not_found(self, client):
        resp = client.get("/api/encounter/species/999")
        assert resp.status_code == 404

    def test_generate_pokemon_endpoint(self, client):
        resp = client.get("/api/encounter/generate/10/5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Pidgey"
        assert data["level"] == 5

    def test_generate_invalid_level(self, client):
        resp = client.get("/api/encounter/generate/10/0")
        assert resp.status_code == 400

    def test_generate_level_too_high(self, client):
        resp = client.get("/api/encounter/generate/10/101")
        assert resp.status_code == 400

    def test_encounter_check_endpoint(self, client):
        resp = client.post("/api/encounter/check", json={"area_id": "route_1"})
        assert resp.status_code == 200
        assert "encountered" in resp.json()
