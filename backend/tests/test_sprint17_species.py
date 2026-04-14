"""Tests for Sprint 17: New Pokemon species."""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)

def _get_species(species_id: int):
    species_data = _load_json("pokemon_species.json")
    return next((s for s in species_data if s.get("id") == species_id), None)


class TestSprint17Species:
    def test_kadabra_exists(self):
        species = _get_species(64)
        assert species is not None
        assert species["name"] == "Kadabra"
        types = [t.lower() for t in species.get("types", [])]
        assert "psychic" in types

    def test_alakazam_exists(self):
        species = _get_species(65)
        assert species is not None
        assert species["name"] == "Alakazam"

    def test_hitmonlee_exists(self):
        species = _get_species(106)
        assert species is not None
        assert species["name"] == "Hitmonlee"
        types = [t.lower() for t in species.get("types", [])]
        assert "fighting" in types

    def test_hitmonchan_exists(self):
        species = _get_species(107)
        assert species is not None
        assert species["name"] == "Hitmonchan"

    def test_mr_mime_exists(self):
        species = _get_species(122)
        assert species is not None
        assert species["name"] == "Mr. Mime"

    def test_abra_evolves_to_kadabra(self):
        species = _get_species(63)
        assert species is not None
        evo = species.get("evolution")
        assert evo is not None
        assert evo.get("to") == 64
        assert evo.get("level") == 16

    def test_all_sprint17_species_have_stats(self):
        for sid in [64, 65, 106, 107, 122]:
            species = _get_species(sid)
            assert species is not None, f"Species {sid} not found"
            stats = species.get("stats", {})
            for stat in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
                assert stat in stats, f"Species {sid} missing stat {stat}"
