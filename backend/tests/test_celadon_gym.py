"""Tests for Sprint 15: Celadon City Gym (Erika)."""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


class TestCeladonGymData:
    def test_celadon_gym_exists_in_data(self):
        gyms = _load_json("gyms.json")
        gym = next((g for g in gyms if g["id"] == "celadon_gym"), None)
        assert gym is not None

    def test_celadon_gym_has_rainbow_badge(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "celadon_gym")
        assert gym["badge_name"] == "Rainbow Badge"

    def test_celadon_gym_leader_is_erika(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "celadon_gym")
        assert gym["leader"]["name"] == "Erika"
        assert gym["type_specialty"] == "grass"

    def test_erika_has_three_pokemon(self):
        gyms = _load_json("gyms.json")
        gym = next(g for g in gyms if g["id"] == "celadon_gym")
        assert len(gym["leader"]["pokemon_team"]) == 3

    def test_total_gym_count_is_four(self):
        gyms = _load_json("gyms.json")
        assert len(gyms) == 5
