"""Tests for Sprint 34: TM/HM compatibility, move tutors, Pokedex entries.

These tests verify TM compatibility mappings, move tutor data,
and complete Pokedex entries for all 151 Pokemon.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── TM/HM Compatibility ─────────────────────────────────────

class TestTMCompatibility:
    def test_tm_count(self):
        compat = _load_json("tm_compatibility.json")
        assert len(compat) == 22

    def test_has_hms(self):
        compat = _load_json("tm_compatibility.json")
        for hm in ["HM01", "HM02", "HM03", "HM04", "HM05"]:
            assert hm in compat

    def test_has_tms(self):
        compat = _load_json("tm_compatibility.json")
        tm_keys = [k for k in compat if k.startswith("TM")]
        assert len(tm_keys) >= 15

    def test_all_entries_have_move(self):
        compat = _load_json("tm_compatibility.json")
        for tm_id, data in compat.items():
            assert "move" in data, f"{tm_id} missing move field"
            assert "compatible_species" in data, f"{tm_id} missing compatible_species"

    def test_all_species_valid(self):
        compat = _load_json("tm_compatibility.json")
        for tm_id, data in compat.items():
            for species_id in data["compatible_species"]:
                assert 1 <= species_id <= 151, f"{tm_id} has invalid species {species_id}"

    def test_toxic_universal(self):
        compat = _load_json("tm_compatibility.json")
        assert len(compat["TM06"]["compatible_species"]) == 151

    def test_surf_water_types(self):
        compat = _load_json("tm_compatibility.json")
        surf_species = compat["HM03"]["compatible_species"]
        # Squirtle line should learn Surf
        for sid in [7, 8, 9]:
            assert sid in surf_species

    def test_fly_flying_types(self):
        compat = _load_json("tm_compatibility.json")
        fly_species = compat["HM02"]["compatible_species"]
        # Charizard and Pidgey line
        assert 6 in fly_species
        assert 18 in fly_species

    def test_cut_species(self):
        compat = _load_json("tm_compatibility.json")
        cut_species = compat["HM01"]["compatible_species"]
        assert len(cut_species) >= 20


# ──── Move Tutors ──────────────────────────────────────────────

class TestMoveTutors:
    def test_tutor_count(self):
        tutors = _load_json("move_tutors.json")
        assert len(tutors) == 5

    def test_all_tutors_have_fields(self):
        tutors = _load_json("move_tutors.json")
        for tutor in tutors:
            assert "id" in tutor
            assert "name" in tutor
            assert "location" in tutor
            assert "moves" in tutor
            assert "cost_type" in tutor

    def test_each_tutor_has_moves(self):
        tutors = _load_json("move_tutors.json")
        for tutor in tutors:
            assert len(tutor["moves"]) >= 3

    def test_cinnabar_tutor_free(self):
        tutors = _load_json("move_tutors.json")
        cinnabar = next(t for t in tutors if t["id"] == "cinnabar_tutor")
        assert cinnabar["cost_type"] == "free"
        assert cinnabar["cost"] == 0

    def test_tutor_moves_valid(self):
        tutors = _load_json("move_tutors.json")
        moves = _load_json("moves.json")
        for tutor in tutors:
            for move_name in tutor["moves"]:
                assert move_name in moves, f"Tutor move {move_name} not in move database"

    EXPECTED_LOCATIONS = ["celadon_city", "fuchsia_city", "saffron_city", "cinnabar_island", "indigo_plateau"]

    @pytest.mark.parametrize("location", EXPECTED_LOCATIONS)
    def test_tutor_at_location(self, location):
        tutors = _load_json("move_tutors.json")
        found = any(t for t in tutors if t["location"] == location)
        assert found, f"No tutor at {location}"


# ──── Pokedex Entries ──────────────────────────────────────────

class TestPokedexEntries:
    def test_entry_count(self):
        entries = _load_json("pokedex_entries.json")
        assert len(entries) == 151

    def test_all_151_present(self):
        entries = _load_json("pokedex_entries.json")
        for i in range(1, 152):
            assert str(i) in entries, f"Pokedex #{i} missing"

    def test_all_entries_have_required_fields(self):
        entries = _load_json("pokedex_entries.json")
        for dex_id, entry in entries.items():
            assert "national_dex" in entry
            assert "name" in entry
            assert "category" in entry
            assert "height_m" in entry
            assert "weight_kg" in entry
            assert "description" in entry

    def test_pikachu_entry(self):
        entries = _load_json("pokedex_entries.json")
        pika = entries["25"]
        assert pika["name"] == "Pikachu"
        assert pika["category"] == "Mouse Pokemon"
        assert pika["height_m"] == 0.4
        assert pika["weight_kg"] == 6.0

    def test_mewtwo_entry(self):
        entries = _load_json("pokedex_entries.json")
        mewtwo = entries["150"]
        assert mewtwo["name"] == "Mewtwo"
        assert mewtwo["category"] == "Genetic Pokemon"

    def test_mew_entry(self):
        entries = _load_json("pokedex_entries.json")
        mew = entries["151"]
        assert mew["name"] == "Mew"
        assert mew["weight_kg"] == 4.0

    def test_all_descriptions_nonempty(self):
        entries = _load_json("pokedex_entries.json")
        for dex_id, entry in entries.items():
            assert len(entry["description"]) >= 20, (
                f"Pokedex #{dex_id} description too short"
            )

    def test_all_heights_positive(self):
        entries = _load_json("pokedex_entries.json")
        for dex_id, entry in entries.items():
            assert entry["height_m"] > 0, f"#{dex_id} height not positive"

    def test_all_weights_positive(self):
        entries = _load_json("pokedex_entries.json")
        for dex_id, entry in entries.items():
            assert entry["weight_kg"] > 0, f"#{dex_id} weight not positive"

    def test_snorlax_heaviest_common(self):
        entries = _load_json("pokedex_entries.json")
        snorlax = entries["143"]
        assert snorlax["weight_kg"] == 460.0

    def test_all_species_have_pokedex_entry(self):
        entries = _load_json("pokedex_entries.json")
        species = _load_json("pokemon_species.json")
        pokedex_names = {e["name"] for e in entries.values()}
        for s in species:
            assert s["name"] in pokedex_names, (
                f"Species {s['name']} not found in Pokedex"
            )


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
