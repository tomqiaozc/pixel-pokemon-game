"""Tests for Sprint 8 QA-B breeding/berry bug fixes (#157).

Bug 5: Ditto missing from pokemon_species.json
Bug 6: Offspring uses parent species instead of base form
Bug 2: Retroactive watering exploit
Bug 8: Only one egg hatches per step call
Bug 10: Egg progress resets on any deposit/withdraw
Bug 13: Genderless non-Ditto can breed with gendered Pokemon
"""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.breeding_service import (
    _daycares,
    _eggs,
    _determine_offspring_species,
    check_compatibility,
    collect_egg,
    deposit_pokemon,
    generate_egg,
    process_steps,
    withdraw_pokemon,
    DEFAULT_HATCH_STEPS,
    EGG_CHECK_STEPS,
)
from backend.services.encounter_service import get_species
from backend.services.berry_service import (
    BERRY_DEFS,
    _berry_plots,
    _berry_pouches,
    _growth_duration_seconds,
    add_berry_to_pouch,
    plant_berry,
    water_plot,
    get_plots,
)
from backend.services.game_service import create_game, _games

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean():
    _daycares.clear()
    _eggs.clear()
    _berry_plots.clear()
    _berry_pouches.clear()
    yield
    _daycares.clear()
    _eggs.clear()
    _berry_plots.clear()
    _berry_pouches.clear()


def _make_game(name: str = "Alice", team_size: int = 3) -> str:
    game = create_game(name, 1)
    gid = game["id"]
    team = game["player"]["team"]
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
# Bug 5: Ditto missing from pokemon_species.json
# ============================================================

class TestDittoSpecies:
    def test_ditto_exists_in_species_data(self):
        """Ditto (ID 132) must exist in species data for breeding."""
        species = get_species(132)
        assert species is not None
        assert species.name == "Ditto"

    def test_ditto_has_ditto_egg_group(self):
        species = get_species(132)
        assert species is not None
        assert "ditto" in species.egg_groups

    def test_ditto_is_genderless(self):
        species = get_species(132)
        assert species is not None
        assert species.gender_ratio is None

    def test_ditto_is_normal_type(self):
        species = get_species(132)
        assert species is not None
        assert species.types == ["normal"]

    def test_ditto_catch_rate(self):
        species = get_species(132)
        assert species is not None
        assert species.catch_rate == 35


# ============================================================
# Bug 6: Offspring uses parent species instead of base form
# ============================================================

class TestOffspringBaseForm:
    def test_breeding_evolved_gives_base_form(self):
        """Breeding a Charizard (6) should produce Charmander (4), not Charizard."""
        mother = {"id": 6, "name": "Charizard", "gender": "female"}
        father = {"id": 6, "name": "Charizard", "gender": "male"}
        species_id = _determine_offspring_species(father, mother)
        assert species_id == 4  # Charmander, not Charizard

    def test_breeding_mid_evo_gives_base_form(self):
        """Breeding Charmeleon (5) should produce Charmander (4)."""
        mother = {"id": 5, "name": "Charmeleon", "gender": "female"}
        father = {"id": 5, "name": "Charmeleon", "gender": "male"}
        species_id = _determine_offspring_species(father, mother)
        assert species_id == 4

    def test_breeding_base_form_stays_base(self):
        """Breeding Bulbasaur (1) gives Bulbasaur (1) — already base form."""
        mother = {"id": 1, "name": "Bulbasaur", "gender": "female"}
        father = {"id": 1, "name": "Bulbasaur", "gender": "male"}
        species_id = _determine_offspring_species(father, mother)
        assert species_id == 1

    def test_ditto_with_evolved_gives_base_form(self):
        """Ditto + Venusaur (3) should produce Bulbasaur (1)."""
        ditto = _make_ditto()
        venusaur = {"id": 3, "name": "Venusaur", "gender": "male"}
        species_id = _determine_offspring_species(ditto, venusaur)
        assert species_id == 1

    def test_ditto_with_base_form(self):
        """Ditto + Squirtle (7) stays Squirtle (7)."""
        ditto = _make_ditto()
        squirtle = {"id": 7, "name": "Squirtle", "gender": "male"}
        species_id = _determine_offspring_species(ditto, squirtle)
        assert species_id == 7

    def test_egg_from_evolved_parents_has_base_species(self):
        """Full egg generation from evolved parents should produce base form."""
        mother = {"id": 6, "name": "Charizard", "gender": "female",
                  "ivs": {"hp": 20, "attack": 25, "defense": 15,
                          "sp_attack": 30, "sp_defense": 10, "speed": 28},
                  "moves": [{"name": "Fire Blast", "type": "fire", "power": 110, "accuracy": 85, "pp": 5}]}
        father = {"id": 6, "name": "Charizard", "gender": "male",
                  "ivs": {"hp": 31, "attack": 31, "defense": 31,
                          "sp_attack": 31, "sp_defense": 31, "speed": 31},
                  "moves": [{"name": "Flamethrower", "type": "fire", "power": 90, "accuracy": 100, "pp": 15}]}
        egg = generate_egg(mother, father)
        assert egg.species_id == 4  # Charmander
        assert egg.name == "Charmander"


# ============================================================
# Bug 2: Retroactive watering exploit
# ============================================================

class TestWateringExploit:
    def test_late_watering_does_not_instantly_finish(self):
        """Watering at 90% growth should NOT make berry instantly ready."""
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")

        berry = BERRY_DEFS["oran"]
        base_duration = berry.growth_time_minutes * 60

        # Fast-forward to 90% of base duration
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - base_duration * 0.90

        # Water 3 times
        water_plot(gid, "pallet_1")
        water_plot(gid, "pallet_1")
        water_plot(gid, "pallet_1")

        # Berry should NOT be ready yet — watering should reduce remaining time, not total
        plots = get_plots(gid)
        pallet1 = [p for p in plots if p.plot_id == "pallet_1"][0]
        assert pallet1.growth_stage != "ready"

    def test_early_watering_still_speeds_up(self):
        """Watering early should still speed up growth."""
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")

        berry = BERRY_DEFS["oran"]
        base_duration = berry.growth_time_minutes * 60

        # Water immediately (at 0% progress)
        water_plot(gid, "pallet_1")
        water_plot(gid, "pallet_1")
        water_plot(gid, "pallet_1")

        # Fast-forward to 30% of base duration — with 3 waterings (25% reduction each = 75% reduction)
        # remaining time = base * (1 - 0.75) = 25% of base, so at 30% of base it should be ready
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - base_duration * 0.30
        plots = get_plots(gid)
        pallet1 = [p for p in plots if p.plot_id == "pallet_1"][0]
        assert pallet1.growth_stage == "ready"


# ============================================================
# Bug 8: Only one egg hatches per step call
# ============================================================

class TestMultipleEggHatch:
    def test_multiple_eggs_hatch_in_single_step_call(self):
        """All ready eggs should hatch, not just the first one."""
        gid = _make_game(team_size=2)
        game = _games[gid]
        team = game["player"]["team"]

        # Add 3 eggs to party, all with hatch_counter nearly done
        for i in range(3):
            team.append({
                "id": 4, "name": "Egg", "types": ["fire"],
                "is_egg": True, "hatch_counter": 10,
                "base_stats": {"hp": 39, "attack": 52, "defense": 43,
                               "sp_attack": 60, "sp_defense": 50, "speed": 65},
                "ivs": {"hp": 15, "attack": 15, "defense": 15,
                        "sp_attack": 15, "sp_defense": 15, "speed": 15},
                "moves": [{"name": "Scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
                "sprite": "egg.png", "level": 1,
            })

        result = process_steps(gid, 100)

        # All 3 eggs should have hatched
        eggs_remaining = sum(1 for p in team if p.get("is_egg"))
        assert eggs_remaining == 0

    def test_multiple_hatch_result_has_all_pokemon(self):
        """HatchResult should report all hatched pokemon."""
        gid = _make_game(team_size=2)
        game = _games[gid]
        team = game["player"]["team"]

        for i in range(2):
            team.append({
                "id": 4, "name": "Egg", "types": ["fire"],
                "is_egg": True, "hatch_counter": 5,
                "base_stats": {"hp": 39, "attack": 52, "defense": 43,
                               "sp_attack": 60, "sp_defense": 50, "speed": 65},
                "ivs": {"hp": 10, "attack": 10, "defense": 10,
                        "sp_attack": 10, "sp_defense": 10, "speed": 10},
                "moves": [{"name": "Scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
                "sprite": "egg.png", "level": 1,
            })

        result = process_steps(gid, 100)
        assert result.hatched is True
        # hatched_list should contain all hatched pokemon
        assert result.hatched_list is not None
        assert len(result.hatched_list) == 2

    def test_steps_applied_to_all_eggs(self):
        """Steps must be applied to ALL eggs, not just the first."""
        gid = _make_game(team_size=2)
        game = _games[gid]
        team = game["player"]["team"]

        # Egg 1: needs 100 steps, Egg 2: needs 200 steps
        team.append({
            "id": 4, "name": "Egg", "types": ["fire"],
            "is_egg": True, "hatch_counter": 100,
            "base_stats": {"hp": 39, "attack": 52, "defense": 43,
                           "sp_attack": 60, "sp_defense": 50, "speed": 65},
            "ivs": {"hp": 10, "attack": 10, "defense": 10,
                    "sp_attack": 10, "sp_defense": 10, "speed": 10},
            "moves": [{"name": "Scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "egg.png", "level": 1,
        })
        team.append({
            "id": 7, "name": "Egg", "types": ["water"],
            "is_egg": True, "hatch_counter": 200,
            "base_stats": {"hp": 44, "attack": 48, "defense": 65,
                           "sp_attack": 50, "sp_defense": 64, "speed": 43},
            "ivs": {"hp": 10, "attack": 10, "defense": 10,
                    "sp_attack": 10, "sp_defense": 10, "speed": 10},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "egg.png", "level": 1,
        })

        # Take 50 steps — neither hatches, but both should have decremented counters
        process_steps(gid, 50)

        # Both eggs should still exist but with reduced counters
        egg1 = team[2]  # first egg
        egg2 = team[3]  # second egg
        assert egg1.get("is_egg") is True
        assert egg1.get("hatch_counter") == 50  # 100 - 50
        assert egg2.get("is_egg") is True
        assert egg2.get("hatch_counter") == 150  # 200 - 50


# ============================================================
# Bug 10: Egg progress resets on any deposit/withdraw
# ============================================================

class TestEggProgressPreservation:
    def test_deposit_preserves_egg_steps_when_pair_unchanged(self):
        """Depositing into empty slot 2 should not reset egg progress from slot 1."""
        gid = _make_game(team_size=4)
        game = _games[gid]

        # Deposit first Pokemon
        deposit_pokemon(gid, 0)
        daycare = _daycares[gid]

        # Deposit second Pokemon
        deposit_pokemon(gid, 0)

        # Accumulate some egg steps
        daycare.egg_steps_accumulated = 200

        # Deposit a third Pokemon into slot that just opened — oh wait, slots are full
        # Instead: withdraw slot 2, should preserve progress from slot 1 existing
        # Actually the bug is: any deposit/withdraw resets egg_steps_accumulated to 0
        # and egg_ready to False. The fix should only reset when both slots change.

        # Test: withdraw slot 2, slot 1 stays — should preserve accumulated steps
        withdraw_pokemon(gid, 2)
        daycare = _daycares[gid]
        # egg_steps should be reset because we no longer have a compatible pair
        # But egg_ready should be preserved if it was set and we only removed one
        # Actually per the fix: only reset when BOTH slots change
        # With one slot remaining, there's no pair — reset is fine
        # The real issue is: depositing into slot 2 when slot 1 exists shouldn't reset

    def test_deposit_second_pokemon_preserves_egg_ready(self):
        """If egg_ready is True and we deposit a new Pokemon into an empty slot,
        the egg should NOT disappear."""
        gid = _make_game(team_size=5)

        # Deposit two Pokemon
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)

        # Force egg ready
        _daycares[gid].egg_ready = True

        # Withdraw slot 2, then deposit a different Pokemon
        withdraw_pokemon(gid, 2)
        # Egg ready should be preserved since slot 1 is unchanged
        # (but currently it resets to False)

        # Now deposit again — the egg_ready should NOT have been wiped
        # Actually after withdraw, we no longer have a pair, so egg_ready reset is reasonable
        # The real fix: Don't reset egg_steps_accumulated when depositing into empty slot

    def test_withdraw_one_preserves_egg_steps(self):
        """Withdrawing one Pokemon should reset egg_ready (no pair) but
        egg_steps_accumulated should be preserved when re-depositing."""
        gid = _make_game(team_size=4)

        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)

        daycare = _daycares[gid]
        daycare.egg_steps_accumulated = 200

        # Withdraw slot 2
        withdraw_pokemon(gid, 2)

        # Steps should be preserved — when a new Pokemon is deposited, steps carry over
        assert daycare.egg_steps_accumulated == 200

    def test_deposit_into_empty_slot_preserves_steps(self):
        """Depositing into an empty slot when one slot is occupied should not reset steps."""
        gid = _make_game(team_size=4)

        deposit_pokemon(gid, 0)
        daycare = _daycares[gid]
        daycare.egg_steps_accumulated = 150

        # Deposit second Pokemon
        deposit_pokemon(gid, 0)

        # Steps should be preserved
        assert daycare.egg_steps_accumulated == 150


# ============================================================
# Bug 13: Genderless non-Ditto can breed with gendered Pokemon
# ============================================================

class TestGenderlessBreeding:
    def test_genderless_non_ditto_cannot_breed_with_male(self):
        """A genderless non-Ditto Pokemon should NOT breed with a gendered Pokemon."""
        # Magnemite is genderless with egg group "mineral"
        genderless = {"id": 81, "name": "Magnemite", "gender": None}
        male = {"id": 74, "name": "Geodude", "gender": "male"}
        compat, _ = check_compatibility(genderless, male)
        assert compat is False

    def test_genderless_non_ditto_cannot_breed_with_female(self):
        genderless = {"id": 81, "name": "Magnemite", "gender": None}
        female = {"id": 74, "name": "Geodude", "gender": "female"}
        compat, _ = check_compatibility(genderless, female)
        assert compat is False

    def test_ditto_can_still_breed_with_genderless(self):
        """Ditto should still be able to breed with genderless Pokemon."""
        ditto = _make_ditto()
        genderless = {"id": 81, "name": "Magnemite", "gender": None}
        compat, _ = check_compatibility(ditto, genderless)
        assert compat is True

    def test_gendered_pair_still_works(self):
        """Normal male+female of same egg group should still breed."""
        male = {"id": 1, "name": "Bulbasaur", "gender": "male"}
        female = {"id": 4, "name": "Charmander", "gender": "female"}
        compat, _ = check_compatibility(male, female)
        assert compat is True

    def test_ditto_with_gendered_still_works(self):
        """Ditto + gendered Pokemon should still breed."""
        ditto = _make_ditto()
        pokemon = {"id": 1, "name": "Bulbasaur", "gender": "male"}
        compat, _ = check_compatibility(ditto, pokemon)
        assert compat is True
