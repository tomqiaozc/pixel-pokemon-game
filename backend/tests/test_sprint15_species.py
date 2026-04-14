"""Tests for Sprint 15: New Pokemon species."""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def _get_species(species_id: int):
    species_data = _load_json("pokemon_species.json")
    return next((s for s in species_data if s.get("id") == species_id), None)


class TestSprint15Species:
    def test_bellsprout_exists(self):
        species = _get_species(69)
        assert species is not None
        assert species["name"] == "Bellsprout"
        types = [t.lower() for t in species.get("types", [])]
        assert "grass" in types
        assert "poison" in types

    def test_weepinbell_exists(self):
        species = _get_species(70)
        assert species is not None
        assert species["name"] == "Weepinbell"
        types = [t.lower() for t in species.get("types", [])]
        assert "grass" in types
        assert "poison" in types

    def test_exeggcute_exists(self):
        species = _get_species(102)
        assert species is not None
        assert species["name"] == "Exeggcute"
        types = [t.lower() for t in species.get("types", [])]
        assert "grass" in types
        assert "psychic" in types

    def test_tangela_exists(self):
        species = _get_species(114)
        assert species is not None
        assert species["name"] == "Tangela"
        types = [t.lower() for t in species.get("types", [])]
        assert "grass" in types

    def test_eevee_exists(self):
        species = _get_species(133)
        assert species is not None
        assert species["name"] == "Eevee"
        types = [t.lower() for t in species.get("types", [])]
        assert "normal" in types

    def test_bellsprout_evolves_to_weepinbell(self):
        species = _get_species(69)
        evo = species.get("evolution")
        assert evo is not None
        assert evo.get("to") == 70
        assert evo.get("level") == 21

    def test_all_sprint15_species_have_stats(self):
        for sid in [69, 70, 102, 114, 133]:
            species = _get_species(sid)
            assert species is not None, f"Species {sid} not found"
            stats = species.get("stats", {})
            for stat in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
                assert stat in stats, f"Species {sid} missing stat {stat}"
                assert stats[stat] > 0, f"Species {sid} has invalid {stat}"
