"""Tests for Sprint 13 QA: New Pokemon species.

These tests verify that the new Pokemon species required for Sprint 13
(Vermilion City / S.S. Anne arc) exist in pokemon_species.json with
correct types and evolution data.
"""
from __future__ import annotations

import json
import os
import pytest

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


def _get_species_by_name(name: str):
    """Look up a species by name."""
    species_data = _load_json("pokemon_species.json")
    if isinstance(species_data, list):
        return next((s for s in species_data if s.get("name") == name), None)
    return None


# ──── Species Existence ────────────────────────────────────

class TestSpeciesExistence:
    def test_pikachu_exists(self):
        species = _get_species_by_name("Pikachu")
        assert species is not None, "Pikachu not found in species data"
        assert species["id"] == 15

    def test_raichu_exists(self):
        species = _get_species_by_name("Raichu")
        assert species is not None, "Raichu not found in species data"
        assert species["id"] == 16

    def test_machop_exists(self):
        species = _get_species(66)
        assert species is not None, "Species 66 (Machop) not found"

    def test_machoke_exists(self):
        species = _get_species(67)
        assert species is not None, "Species 67 (Machoke) not found"

    def test_magnemite_exists(self):
        species = _get_species(81)
        assert species is not None, "Species 81 (Magnemite) not found"

    def test_magneton_exists(self):
        species = _get_species(82)
        assert species is not None, "Species 82 (Magneton) not found"

    def test_voltorb_exists(self):
        species = _get_species(100)
        assert species is not None, "Species 100 (Voltorb) not found"


# ──── Species Types ────────────────────────────────────────

class TestSpeciesTypes:
    def test_pikachu_type(self):
        species = _get_species_by_name("Pikachu")
        assert species is not None
        types = [t.lower() for t in species.get("types", [])]
        assert "electric" in types

    def test_voltorb_type(self):
        species = _get_species(100)
        assert species is not None
        types = [t.lower() for t in species.get("types", [])]
        assert "electric" in types

    def test_machop_type(self):
        species = _get_species(66)
        assert species is not None
        types = [t.lower() for t in species.get("types", [])]
        assert "fighting" in types

    def test_magnemite_type(self):
        species = _get_species(81)
        assert species is not None
        types = [t.lower() for t in species.get("types", [])]
        assert "electric" in types


# ──── Species Evolution ────────────────────────────────────

class TestSpeciesEvolution:
    def test_pikachu_evolution(self):
        """Pikachu (id:15) should evolve to Raichu (id:16) via stone."""
        species = _get_species_by_name("Pikachu")
        assert species is not None
        evo = species.get("evolution")
        assert evo is not None, "Pikachu should have evolution data"
        assert evo.get("to") == 16
        assert evo.get("item") == "Thunder_Stone"

    def test_machop_evolution(self):
        """Machop (id:66) should evolve to Machoke (id:67) at level 28."""
        species = _get_species(66)
        assert species is not None
        evo = species.get("evolution")
        assert evo is not None
        assert evo.get("to") == 67
        assert evo.get("level") == 28

    def test_magnemite_evolution(self):
        """Magnemite (id:81) should evolve to Magneton (id:82)."""
        species = _get_species(81)
        assert species is not None
        evo = species.get("evolution")
        assert evo is not None
        assert evo.get("to") == 82
