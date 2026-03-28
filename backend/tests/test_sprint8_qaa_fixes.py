"""Tests for Sprint 8 QA-A backend bug fixes (#159).

Bug 1: _hatch_egg() crashes when base_stats is explicitly None
Bug 2: Starter Pokemon missing gender key after create_game()
Bug 3: /step endpoint returns 500 on ValueError instead of 400
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.breeding_service import (
    _daycares,
    _eggs,
    _hatch_egg,
    process_steps,
    DEFAULT_HATCH_STEPS,
)
from backend.services.game_service import create_game, _games
from backend.services.encounter_service import get_species

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean():
    _daycares.clear()
    _eggs.clear()
    yield
    _daycares.clear()
    _eggs.clear()


# ============================================================
# Bug 1: _hatch_egg() crashes on base_stats=None
# ============================================================

class TestHatchEggBaseStatsNone:
    def test_hatch_egg_with_base_stats_none(self):
        """_hatch_egg should not crash when base_stats is explicitly None."""
        egg = {
            "species_id": 1,
            "name": "Bulbasaur",
            "types": ["grass", "poison"],
            "ivs": {"hp": 15, "attack": 15, "defense": 15,
                    "sp_attack": 15, "sp_defense": 15, "speed": 15},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "base_stats": None,  # Explicitly None — this causes the crash
            "is_egg": True,
            "hatch_counter": 0,
            "sprite": "egg.png",
            "level": 1,
        }
        hatched = _hatch_egg(egg)
        assert hatched["name"] == "Bulbasaur"
        assert hatched["is_egg"] is False
        assert hatched["stats"]["hp"] > 0

    def test_hatch_egg_with_base_stats_missing(self):
        """_hatch_egg should work when base_stats key is missing entirely."""
        egg = {
            "species_id": 1,
            "name": "Bulbasaur",
            "types": ["grass", "poison"],
            "ivs": {"hp": 15, "attack": 15, "defense": 15,
                    "sp_attack": 15, "sp_defense": 15, "speed": 15},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "is_egg": True,
            "hatch_counter": 0,
            "sprite": "egg.png",
            "level": 1,
        }
        hatched = _hatch_egg(egg)
        assert hatched["name"] == "Bulbasaur"
        assert hatched["is_egg"] is False

    def test_hatch_egg_with_base_stats_present(self):
        """_hatch_egg should work normally when base_stats is present."""
        egg = {
            "species_id": 4,
            "name": "Charmander",
            "types": ["fire"],
            "ivs": {"hp": 20, "attack": 20, "defense": 20,
                    "sp_attack": 20, "sp_defense": 20, "speed": 20},
            "moves": [{"name": "Scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "base_stats": {"hp": 39, "attack": 52, "defense": 43,
                          "sp_attack": 60, "sp_defense": 50, "speed": 65},
            "is_egg": True,
            "hatch_counter": 0,
            "sprite": "egg.png",
            "level": 1,
        }
        hatched = _hatch_egg(egg)
        assert hatched["name"] == "Charmander"
        assert hatched["is_egg"] is False

    def test_process_steps_hatches_egg_with_none_base_stats(self):
        """Full process_steps flow should not crash on egg with base_stats=None."""
        game = create_game("Alice", 1)
        gid = game["id"]
        team = game["player"]["team"]
        team.append({
            "id": 1, "name": "Egg", "types": ["grass"],
            "is_egg": True, "hatch_counter": 10,
            "base_stats": None,
            "ivs": {"hp": 10, "attack": 10, "defense": 10,
                    "sp_attack": 10, "sp_defense": 10, "speed": 10},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "egg.png", "level": 1,
        })
        result = process_steps(gid, 100)
        assert result.hatched is True


# ============================================================
# Bug 2: Starter Pokemon missing gender key
# ============================================================

class TestStarterGender:
    def test_starter_has_gender_key(self):
        """create_game() starter should have a gender field."""
        game = create_game("Bob", 1)  # Bulbasaur
        starter = game["player"]["team"][0]
        assert "gender" in starter

    def test_starter_gender_matches_species(self):
        """Starter gender should be based on species gender_ratio."""
        # Bulbasaur has gender_ratio 12.5 (87.5% male)
        game = create_game("Carol", 1)
        starter = game["player"]["team"][0]
        assert starter["gender"] in ("male", "female")

    def test_starter_gender_is_set_not_excluded(self):
        """The gender field should persist even through model_dump(exclude_none=True)
        because gendered starters should have gender explicitly set."""
        # Run 20 times to check it's consistent (not random None vs present)
        for _ in range(20):
            game = create_game("Dan", 1)
            starter = game["player"]["team"][0]
            assert "gender" in starter, "gender key must always be present on starter"


# ============================================================
# Bug 3: /step endpoint missing ValueError catch
# ============================================================

class TestStepEndpointErrorHandling:
    def test_step_with_invalid_game_id(self):
        """Step endpoint should return 404 for non-existent game."""
        resp = client.post("/api/daycare/step", json={"game_id": "nonexistent", "steps": 10})
        assert resp.status_code == 404

    def test_step_with_negative_steps(self):
        """Step endpoint should handle negative steps gracefully (not 500)."""
        game = create_game("Eve", 1)
        gid = game["id"]
        resp = client.post("/api/daycare/step", json={"game_id": gid, "steps": -5})
        assert resp.status_code in (200, 400)  # Either 200 (no-op) or 400, not 500

    def test_step_with_zero_steps(self):
        """Step endpoint should handle zero steps gracefully."""
        game = create_game("Frank", 1)
        gid = game["id"]
        resp = client.post("/api/daycare/step", json={"game_id": gid, "steps": 0})
        assert resp.status_code == 200

    def test_step_with_valid_input(self):
        """Step endpoint should work normally with valid input."""
        game = create_game("Grace", 1)
        gid = game["id"]
        resp = client.post("/api/daycare/step", json={"game_id": gid, "steps": 100})
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
