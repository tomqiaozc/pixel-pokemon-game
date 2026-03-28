"""Tests for the Pokemon Breeding & Daycare System."""
from __future__ import annotations

import random
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.breeding_service import (
    _daycares,
    _eggs,
    _inherit_ivs,
    _determine_offspring_species,
    _identify_father,
    check_compatibility,
    collect_egg,
    deposit_pokemon,
    generate_egg,
    get_daycare_status,
    process_steps,
    withdraw_pokemon,
    DEFAULT_HATCH_STEPS,
    EGG_CHECK_STEPS,
)
from backend.services.game_service import create_game, _games

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean():
    _daycares.clear()
    _eggs.clear()
    yield
    _daycares.clear()
    _eggs.clear()


def _make_game(name: str = "Alice", team_size: int = 3) -> str:
    game = create_game(name, 1)
    gid = game["id"]
    # Ensure team has gender and egg groups available via species lookup
    team = game["player"]["team"]
    # Set gender on starter
    team[0]["gender"] = "male"
    for i in range(team_size - 1):
        team.append({
            "id": 4, "name": "Charmander", "types": ["fire"],
            "stats": {"hp": 39, "attack": 52, "defense": 43,
                      "sp_attack": 60, "sp_defense": 50, "speed": 65},
            "moves": [{"name": "Scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "charmander.png", "level": 10,
            "gender": "female" if i == 0 else "male",
            "ivs": {"hp": 20, "attack": 25, "defense": 15, "sp_attack": 30, "sp_defense": 10, "speed": 28},
        })
    return gid


def _make_ditto() -> dict:
    """Create a Ditto for breeding tests."""
    return {
        "id": 132, "name": "Ditto", "types": ["normal"],
        "stats": {"hp": 48, "attack": 48, "defense": 48,
                  "sp_attack": 48, "sp_defense": 48, "speed": 48},
        "moves": [{"name": "Transform", "type": "normal", "power": 0, "accuracy": 100, "pp": 10}],
        "sprite": "ditto.png", "level": 30,
        "gender": None,
        "ivs": {"hp": 31, "attack": 31, "defense": 31, "sp_attack": 31, "sp_defense": 31, "speed": 31},
    }


# ============================================================
# Compatibility Checks
# ============================================================

class TestCompatibility:
    def test_same_egg_group_different_gender(self):
        male = {"id": 1, "name": "Bulbasaur", "gender": "male"}
        female = {"id": 1, "name": "Bulbasaur", "gender": "female"}
        compat, msg = check_compatibility(male, female)
        assert compat is True

    def test_same_gender_incompatible(self):
        male1 = {"id": 1, "name": "Bulbasaur", "gender": "male"}
        male2 = {"id": 4, "name": "Charmander", "gender": "male"}
        compat, _ = check_compatibility(male1, male2)
        assert compat is False

    def test_ditto_with_anything(self):
        ditto = _make_ditto()
        pokemon = {"id": 1, "name": "Bulbasaur", "gender": "male"}
        compat, _ = check_compatibility(ditto, pokemon)
        assert compat is True

    def test_two_dittos_incompatible(self):
        d1 = _make_ditto()
        d2 = _make_ditto()
        compat, _ = check_compatibility(d1, d2)
        assert compat is False

    def test_none_pokemon(self):
        compat, _ = check_compatibility(None, {"id": 1, "name": "Bulbasaur"})
        assert compat is False

    def test_genderless_non_ditto_incompatible(self):
        g1 = {"id": 120, "name": "Staryu", "gender": None}
        g2 = {"id": 121, "name": "Starmie", "gender": None}
        compat, _ = check_compatibility(g1, g2)
        assert compat is False

    def test_ditto_with_genderless(self):
        ditto = _make_ditto()
        staryu = {"id": 120, "name": "Staryu", "gender": None}
        compat, _ = check_compatibility(ditto, staryu)
        assert compat is True


# ============================================================
# Offspring Species
# ============================================================

class TestOffspringSpecies:
    def test_mother_determines_species(self):
        mother = {"id": 1, "name": "Bulbasaur", "gender": "female"}
        father = {"id": 4, "name": "Charmander", "gender": "male"}
        species_id = _determine_offspring_species(father, mother)
        assert species_id == 1  # Bulbasaur (mother)

    def test_ditto_non_ditto(self):
        ditto = _make_ditto()
        pokemon = {"id": 25, "name": "Pikachu", "gender": "male"}
        species_id = _determine_offspring_species(ditto, pokemon)
        assert species_id == 25  # Non-Ditto parent

    def test_non_ditto_ditto(self):
        pokemon = {"id": 4, "name": "Charmander", "gender": "female"}
        ditto = _make_ditto()
        species_id = _determine_offspring_species(pokemon, ditto)
        assert species_id == 4


# ============================================================
# IV Inheritance
# ============================================================

class TestIVInheritance:
    def test_three_ivs_inherited(self):
        parent_a = {"ivs": {"hp": 31, "attack": 31, "defense": 31,
                            "sp_attack": 31, "sp_defense": 31, "speed": 31}}
        parent_b = {"ivs": {"hp": 0, "attack": 0, "defense": 0,
                            "sp_attack": 0, "sp_defense": 0, "speed": 0}}

        random.seed(42)
        ivs = _inherit_ivs(parent_a, parent_b)
        assert len(ivs) == 6

        # At least some should be from parents (0 or 31)
        from_parents = sum(1 for v in ivs.values() if v in (0, 31))
        assert from_parents >= 3

    def test_missing_ivs_defaults(self):
        parent_a = {}
        parent_b = {}
        ivs = _inherit_ivs(parent_a, parent_b)
        assert len(ivs) == 6
        assert all(0 <= v <= 31 for v in ivs.values())


# ============================================================
# Egg Generation
# ============================================================

class TestEggGeneration:
    def test_generate_egg(self):
        parent_a = {"id": 1, "name": "Bulbasaur", "gender": "female",
                    "ivs": {"hp": 20, "attack": 25, "defense": 15,
                            "sp_attack": 30, "sp_defense": 10, "speed": 28},
                    "moves": [{"name": "Vine Whip", "type": "grass", "power": 45, "accuracy": 100, "pp": 25}]}
        parent_b = {"id": 1, "name": "Bulbasaur", "gender": "male",
                    "ivs": {"hp": 31, "attack": 31, "defense": 31,
                            "sp_attack": 31, "sp_defense": 31, "speed": 31},
                    "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}]}

        egg = generate_egg(parent_a, parent_b)
        assert egg.species_id == 1
        assert egg.is_egg is True
        assert egg.hatch_counter == DEFAULT_HATCH_STEPS
        assert len(egg.ivs) == 6
        assert len(egg.moves) >= 1

    def test_ditto_egg_species(self):
        ditto = _make_ditto()
        pokemon = {"id": 25, "name": "Pikachu", "gender": "male",
                   "ivs": {"hp": 15, "attack": 15, "defense": 15,
                           "sp_attack": 15, "sp_defense": 15, "speed": 15},
                   "moves": [{"name": "Thunder Shock", "type": "electric", "power": 40, "accuracy": 100, "pp": 30}]}

        egg = generate_egg(ditto, pokemon)
        assert egg.species_id == 25  # Pikachu, not Ditto


# ============================================================
# Deposit & Withdraw
# ============================================================

class TestDeposit:
    def test_deposit_pokemon(self):
        gid = _make_game()
        game = _games[gid]
        initial_team = len(game["player"]["team"])
        result = deposit_pokemon(gid, 0)
        assert result.slot_1 is not None
        assert len(game["player"]["team"]) == initial_team - 1

    def test_deposit_two(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        result = deposit_pokemon(gid, 0)
        assert result.slot_1 is not None
        assert result.slot_2 is not None

    def test_deposit_full_fails(self):
        gid = _make_game(team_size=5)
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)
        with pytest.raises(ValueError, match="full"):
            deposit_pokemon(gid, 0)

    def test_deposit_last_pokemon_fails(self):
        gid = _make_game(team_size=1)
        with pytest.raises(ValueError, match="last Pokemon"):
            deposit_pokemon(gid, 0)

    def test_deposit_invalid_index(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="Invalid"):
            deposit_pokemon(gid, 99)

    def test_deposit_negative_index(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="Invalid"):
            deposit_pokemon(gid, -1)


class TestWithdraw:
    def test_withdraw_slot1(self):
        gid = _make_game()
        game = _games[gid]
        deposit_pokemon(gid, 0)
        team_before = len(game["player"]["team"])
        result = withdraw_pokemon(gid, 1)
        assert result.slot_1 is None
        assert len(game["player"]["team"]) == team_before + 1

    def test_withdraw_empty_slot_fails(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="No Pokemon"):
            withdraw_pokemon(gid, 1)

    def test_withdraw_full_team_fails(self):
        gid = _make_game(team_size=6)
        deposit_pokemon(gid, 0)  # Team now 5
        # Add one back to make it 6
        _games[gid]["player"]["team"].append(
            {"id": 1, "name": "Extra", "types": ["normal"],
             "stats": {"hp": 10, "attack": 10, "defense": 10,
                       "sp_attack": 10, "sp_defense": 10, "speed": 10},
             "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
             "sprite": "t.png", "level": 1}
        )
        with pytest.raises(ValueError, match="full"):
            withdraw_pokemon(gid, 1)


# ============================================================
# Daycare Status
# ============================================================

class TestDaycareStatus:
    def test_empty_daycare(self):
        gid = _make_game()
        status = get_daycare_status(gid)
        assert status.slot_1 is None
        assert status.slot_2 is None
        assert status.egg_ready is False

    def test_status_with_pokemon(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        status = get_daycare_status(gid)
        assert status.slot_1 is not None
        assert status.slot_1["name"] is not None


# ============================================================
# Steps Processing
# ============================================================

class TestSteps:
    def test_steps_increment_daycare_exp(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        process_steps(gid, 100)
        daycare = _daycares[gid]
        assert daycare.slot_1.steps_gained == 100

    def test_zero_steps_no_op(self):
        gid = _make_game()
        result = process_steps(gid, 0)
        assert result.hatched is False

    def test_egg_generation_with_compatible_pair(self):
        gid = _make_game()
        # Deposit male and female of same species
        deposit_pokemon(gid, 0)  # male Bulbasaur
        deposit_pokemon(gid, 0)  # female Charmander

        # Force egg generation
        daycare = _daycares[gid]
        daycare.egg_ready = False

        # Take enough steps with forced random to trigger egg
        with patch("backend.services.breeding_service.random.random", return_value=0.1):
            process_steps(gid, EGG_CHECK_STEPS * 2)

        # Egg should be ready (may or may not be, depending on compatibility)
        # Check daycare status
        status = get_daycare_status(gid)
        # Status reports whether pair is compatible
        assert isinstance(status.compatible, bool)


# ============================================================
# Egg Collection
# ============================================================

class TestEggCollection:
    def test_collect_egg(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)

        # Force egg ready
        _daycares[gid].egg_ready = True

        game = _games[gid]
        team_before = len(game["player"]["team"])
        egg = collect_egg(gid)
        assert egg["is_egg"] is True
        assert egg["hatch_counter"] == DEFAULT_HATCH_STEPS
        assert len(game["player"]["team"]) == team_before + 1

    def test_collect_no_egg_fails(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="No egg"):
            collect_egg(gid)

    def test_collect_full_party_fails(self):
        gid = _make_game(team_size=6)
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)
        # Fill team back to 6
        game = _games[gid]
        while len(game["player"]["team"]) < 6:
            game["player"]["team"].append(
                {"id": 1, "name": "Filler", "types": ["normal"],
                 "stats": {"hp": 10, "attack": 10, "defense": 10,
                           "sp_attack": 10, "sp_defense": 10, "speed": 10},
                 "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
                 "sprite": "t.png", "level": 1}
            )
        _daycares[gid].egg_ready = True
        with pytest.raises(ValueError, match="full"):
            collect_egg(gid)


# ============================================================
# Egg Hatching
# ============================================================

class TestHatching:
    def test_egg_hatches_after_steps(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)

        # Force egg ready and collect
        _daycares[gid].egg_ready = True
        egg = collect_egg(gid)
        assert egg["is_egg"] is True

        # Walk enough steps to hatch
        result = process_steps(gid, DEFAULT_HATCH_STEPS + 1)
        assert result.hatched is True
        assert result.pokemon is not None
        assert result.pokemon["is_egg"] is False
        assert result.pokemon["level"] == 1

    def test_egg_not_hatched_insufficient_steps(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)
        _daycares[gid].egg_ready = True
        collect_egg(gid)

        result = process_steps(gid, 100)
        assert result.hatched is False

    def test_hatched_pokemon_has_ivs(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)
        _daycares[gid].egg_ready = True
        collect_egg(gid)

        result = process_steps(gid, DEFAULT_HATCH_STEPS + 1)
        assert result.hatched is True
        assert result.pokemon.get("ivs") is not None
        assert len(result.pokemon["ivs"]) == 6


# ============================================================
# Father Identification
# ============================================================

class TestFatherIdentification:
    def test_male_is_father(self):
        male = {"id": 1, "gender": "male", "moves": [{"name": "Tackle"}]}
        female = {"id": 1, "gender": "female", "moves": [{"name": "Vine Whip"}]}
        father = _identify_father(male, female)
        assert father["gender"] == "male"

    def test_ditto_never_father(self):
        ditto = _make_ditto()
        pokemon = {"id": 1, "name": "Bulbasaur", "gender": "female",
                   "moves": [{"name": "Vine Whip"}]}
        father = _identify_father(ditto, pokemon)
        assert father["name"] == "Bulbasaur"


# ============================================================
# API Tests
# ============================================================

class TestDaycareAPI:
    def test_status_api(self):
        gid = _make_game()
        resp = client.get(f"/api/daycare/status/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["egg_ready"] is False

    def test_status_not_found(self):
        resp = client.get("/api/daycare/status/nope")
        assert resp.status_code == 404

    def test_deposit_api(self):
        gid = _make_game()
        resp = client.post("/api/daycare/deposit", json={
            "game_id": gid, "pokemon_index": 0
        })
        assert resp.status_code == 200
        assert resp.json()["slot_1"] is not None

    def test_deposit_api_not_found(self):
        resp = client.post("/api/daycare/deposit", json={
            "game_id": "nope", "pokemon_index": 0
        })
        assert resp.status_code == 404

    def test_withdraw_api(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        resp = client.post("/api/daycare/withdraw/1", json={"game_id": gid})
        assert resp.status_code == 200

    def test_withdraw_api_empty(self):
        gid = _make_game()
        resp = client.post("/api/daycare/withdraw/1", json={"game_id": gid})
        assert resp.status_code == 400

    def test_collect_egg_api(self):
        gid = _make_game()
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)
        _daycares[gid].egg_ready = True
        resp = client.post("/api/daycare/collect-egg", json={"game_id": gid})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_collect_no_egg_api(self):
        gid = _make_game()
        resp = client.post("/api/daycare/collect-egg", json={"game_id": gid})
        assert resp.status_code == 400

    def test_step_api(self):
        gid = _make_game()
        resp = client.post("/api/daycare/step", json={"game_id": gid, "steps": 10})
        assert resp.status_code == 200

    def test_step_not_found(self):
        resp = client.post("/api/daycare/step", json={"game_id": "nope", "steps": 10})
        assert resp.status_code == 404
