"""Tests for Sprint 14 QA: New Pokemon species.

These tests verify that the new Pokemon species required for Sprint 14
(Lavender Town / Pokemon Tower arc) exist in pokemon_species.json with
correct types and evolution data.
"""
from __future__ import annotations

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def _get_species(species_id: int):
    """Look up a species by numeric id from pokemon_species.json."""
    species_data = _load_json("pokemon_species.json")
    if isinstance(species_data, list):
        return next((s for s in species_data if s.get("id") == species_id), None)
    return None


# ──── Species Existence ──────────────────────────────────

class TestSpeciesExistence:
    def test_gastly_exists(self):
        species = _get_species(92)
        assert species is not None, "Species 92 (Gastly) not found"

    def test_haunter_exists(self):
        species = _get_species(93)
        assert species is not None, "Species 93 (Haunter) not found"

    def test_cubone_exists(self):
        species = _get_species(104)
        assert species is not None, "Species 104 (Cubone) not found"

    def test_marowak_exists(self):
        species = _get_species(105)
        assert species is not None, "Species 105 (Marowak) not found"

    def test_drowzee_exists(self):
        species = _get_species(96)
        assert species is not None, "Species 96 (Drowzee) not found"

    def test_hypno_exists(self):
        species = _get_species(97)
        assert species is not None, "Species 97 (Hypno) not found"


# ──── Species Types ──────────────────────────────────────

class TestSpeciesTypes:
    def test_gastly_type(self):
        species = _get_species(92)
        assert species is not None
        types = [t.lower() for t in species.get("types", [])]
        assert "ghost" in types
        assert "poison" in types

    def test_cubone_type(self):
        species = _get_species(104)
        assert species is not None
        types = [t.lower() for t in species.get("types", [])]
        assert "ground" in types

    def test_drowzee_type(self):
        species = _get_species(96)
        assert species is not None
        types = [t.lower() for t in species.get("types", [])]
        assert "psychic" in types

    def test_hypno_type(self):
        species = _get_species(97)
        assert species is not None
        types = [t.lower() for t in species.get("types", [])]
        assert "psychic" in types


# ──── Species Evolution ──────────────────────────────────

class TestSpeciesEvolution:
    def test_cubone_evolution(self):
        """Cubone (id:104) should evolve to Marowak (id:105) at level 28."""
        species = _get_species(104)
        assert species is not None
        evo = species.get("evolution")
        assert evo is not None, "Cubone should have evolution data"
        assert evo.get("to") == 105
        assert evo.get("level") == 28
