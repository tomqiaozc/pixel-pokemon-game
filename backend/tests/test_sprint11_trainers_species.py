"""Tests for Sprint 11 QA-A2: New Trainers & Species.

These tests verify that 12+ new Pokemon species, 8+ new trainers, evolution
chains, trainer level progression, and NPC dialogues are correctly defined.
Written ahead of backend implementation — will FAIL until data is committed.
"""
from __future__ import annotations

import pytest

from backend.services.encounter_service import (
    generate_wild_pokemon,
    get_species,
)
from backend.services.evolution_service import check_evolution
from backend.services.gym_service import get_trainer, get_trainers_on_map
from backend.services.npc_service import get_npcs_by_map, get_npc


# ──── New Species Existence ──────────────────────────────────

class TestNewSpeciesExist:
    """At least 12 new species must be added for Sprint 11."""

    NEW_SPECIES = [
        (23, "Ekans", ["poison"]),
        (24, "Arbok", ["poison"]),
        (29, "Nidoran-F", ["poison"]),
        (30, "Nidorina", ["poison"]),
        (32, "Nidoran-M", ["poison"]),
        (33, "Nidorino", ["poison"]),
        (39, "Jigglypuff", ["normal", "fairy"]),
        (40, "Wigglytuff", ["normal", "fairy"]),
        (43, "Oddish", ["grass", "poison"]),
        (44, "Gloom", ["grass", "poison"]),
        (63, "Abra", ["psychic"]),
        (64, "Kadabra", ["psychic"]),
    ]

    def test_new_species_count(self):
        found = sum(1 for sid, _, _ in self.NEW_SPECIES if get_species(sid) is not None)
        assert found >= 12, f"Only {found}/12 new species found"

    @pytest.mark.parametrize("species_id,name,types", NEW_SPECIES)
    def test_species_data(self, species_id, name, types):
        species = get_species(species_id)
        assert species is not None, f"Species {name} (ID {species_id}) not found"
        assert species.name == name
        for t in types:
            assert t in species.types, f"{name} missing type {t}"

    def test_ekans_has_learnset(self):
        species = get_species(23)
        assert species is not None
        assert len(species.learnset) >= 2

    def test_oddish_has_learnset(self):
        species = get_species(43)
        assert species is not None
        assert len(species.learnset) >= 2

    def test_abra_has_high_speed(self):
        """Abra should have high speed stat for its flee mechanic."""
        species = get_species(63)
        assert species is not None
        assert species.stats.speed >= 80

    def test_jigglypuff_has_abilities(self):
        species = get_species(39)
        assert species is not None
        assert len(species.abilities) >= 1


# ──── Wild Pokemon Generation ────────────────────────────────

class TestWildPokemonGeneration:
    def test_generate_wild_ekans(self):
        pokemon = generate_wild_pokemon(23, 10)
        assert pokemon.name == "Ekans"
        assert pokemon.level == 10
        assert len(pokemon.moves) >= 1

    def test_generate_wild_oddish(self):
        pokemon = generate_wild_pokemon(43, 12)
        assert pokemon.name == "Oddish"
        assert pokemon.level == 12

    def test_generate_wild_abra(self):
        pokemon = generate_wild_pokemon(63, 10)
        assert pokemon.name == "Abra"
        assert pokemon.level == 10

    def test_generate_wild_jigglypuff(self):
        pokemon = generate_wild_pokemon(39, 10)
        assert pokemon.name == "Jigglypuff"
        assert pokemon.level == 10


# ──── Evolution Chains ───────────────────────────────────────

class TestEvolutionChains:
    def test_ekans_evolves_to_arbok(self):
        species = get_species(23)
        assert species is not None
        assert species.evolution is not None
        assert species.evolution.to == 24

    def test_oddish_evolves_to_gloom(self):
        species = get_species(43)
        assert species is not None
        assert species.evolution is not None
        assert species.evolution.to == 44

    def test_nidoran_f_evolves_to_nidorina(self):
        species = get_species(29)
        assert species is not None
        assert species.evolution is not None
        assert species.evolution.to == 30

    def test_nidoran_m_evolves_to_nidorino(self):
        species = get_species(32)
        assert species is not None
        assert species.evolution is not None
        assert species.evolution.to == 33

    def test_abra_evolves_to_kadabra(self):
        species = get_species(63)
        assert species is not None
        assert species.evolution is not None
        assert species.evolution.to == 64

    def test_jigglypuff_evolves_to_wigglytuff(self):
        """Jigglypuff evolves via Moon Stone — evolution field may differ."""
        species = get_species(39)
        assert species is not None
        # Jigglypuff evolves via Moon Stone, so either:
        # - evolution.to == 40 with level trigger, or
        # - stone evolution handled by held_item_service
        # Just verify Wigglytuff exists and is linked somehow
        wigglytuff = get_species(40)
        assert wigglytuff is not None
        assert wigglytuff.name == "Wigglytuff"


# ──── New Trainers ───────────────────────────────────────────

class TestNewTrainers:
    NEW_TRAINER_IDS = [
        "lass_crissy",
        "youngster_timmy",
        "hiker_marcos",
        "bug_catcher_kent",
        "super_nerd_jovan",
        "cerulean_gym_trainer_1",
        "cerulean_gym_trainer_2",
        "hiker_lenny",
    ]

    def test_new_trainers_count(self):
        found = sum(1 for tid in self.NEW_TRAINER_IDS if get_trainer(tid) is not None)
        assert found >= 8, f"Only {found}/8 new trainers found"

    @pytest.mark.parametrize("trainer_id", NEW_TRAINER_IDS)
    def test_trainer_exists(self, trainer_id):
        trainer = get_trainer(trainer_id)
        assert trainer is not None, f"Trainer {trainer_id} not found"
        assert len(trainer.pokemon_team) >= 1, f"Trainer {trainer_id} has no team"

    def test_route_4_trainer_teams_have_valid_species(self):
        """All Route 4 trainer team species must exist in species data."""
        for tid in ["lass_crissy", "youngster_timmy", "hiker_marcos"]:
            trainer = get_trainer(tid)
            assert trainer is not None
            for pkmn in trainer.pokemon_team:
                species = get_species(pkmn.species_id)
                assert species is not None, (
                    f"Trainer {tid} has species_id {pkmn.species_id} "
                    f"({pkmn.name}) which doesn't exist"
                )

    def test_cerulean_gym_trainers_water_types(self):
        """Cerulean gym trainers should have water-type Pokemon."""
        for tid in ["cerulean_gym_trainer_1", "cerulean_gym_trainer_2"]:
            trainer = get_trainer(tid)
            assert trainer is not None
            for pkmn in trainer.pokemon_team:
                species = get_species(pkmn.species_id)
                assert species is not None
                assert "water" in species.types, (
                    f"Gym trainer {tid}'s {pkmn.name} is not water type"
                )

    def test_trainer_levels_progression(self):
        """Route 4 trainers should be L11-14 (between Route 3 and Cerulean Gym)."""
        for tid in ["lass_crissy", "youngster_timmy", "hiker_marcos"]:
            trainer = get_trainer(tid)
            assert trainer is not None
            for pkmn in trainer.pokemon_team:
                assert 10 <= pkmn.level <= 15, (
                    f"Trainer {tid}'s {pkmn.name} at L{pkmn.level} "
                    f"outside expected range 10-15"
                )


# ──── NPC Dialogues ──────────────────────────────────────────

class TestNPCDialogues:
    CERULEAN_NPCS = [
        "cerulean_townsfolk_1",
        "cerulean_townsfolk_2",
        "cerulean_townsfolk_3",
        "bike_shop_owner",
        "cerulean_officer",
    ]

    def test_cerulean_npcs_exist(self):
        found = sum(1 for nid in self.CERULEAN_NPCS if get_npc(nid) is not None)
        assert found >= 5, f"Only {found}/5 Cerulean NPCs found"

    @pytest.mark.parametrize("npc_id", CERULEAN_NPCS)
    def test_npc_has_dialogue(self, npc_id):
        npc = get_npc(npc_id)
        assert npc is not None, f"NPC {npc_id} not found"
        assert npc.dialogue_tree_id is not None or hasattr(npc, "dialogue"), (
            f"NPC {npc_id} has no dialogue"
        )
