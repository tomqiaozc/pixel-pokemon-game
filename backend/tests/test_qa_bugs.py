"""Tests for Sprint 5 QA-A bug fixes: toxic/confusion/flinch moves, Water Veil, Wonder Guard, Moxie."""
from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from backend.models.battle import BattlePokemon, BattleState, StatStages, StatusEvent
from backend.models.pokemon import Move, Stats
from backend.models.weather import WeatherState
from backend.services.status_service import (
    apply_status,
    process_move_effects,
    process_status_before_move,
)
from backend.services.ability_service import (
    ability_prevents_status,
    check_ability_type_immunity,
    process_ability_on_ko,
)


def _make_pokemon(**overrides) -> BattlePokemon:
    defaults = dict(
        species_id=1,
        name="TestMon",
        types=["normal"],
        level=50,
        stats=Stats(hp=200, attack=100, defense=100, sp_attack=100, sp_defense=100, speed=100),
        current_hp=200,
        max_hp=200,
        moves=[Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)],
        sprite="test.png",
    )
    defaults.update(overrides)
    return BattlePokemon(**defaults)


def _make_move(**overrides) -> Move:
    defaults = dict(name="Tackle", type="normal", power=40, accuracy=100, pp=35)
    defaults.update(overrides)
    return Move(**defaults)


# ============================================================
# BE-02: Toxic move inflicts tox status
# ============================================================

class TestToxicMove:
    def test_toxic_applies_tox_status(self):
        attacker = _make_pokemon(name="Attacker")
        defender = _make_pokemon(name="Defender")
        with patch("backend.services.status_service.random") as mock_random:
            mock_random.randint.return_value = 1  # always hits chance
            events = process_move_effects("Toxic", attacker, defender, "player", "enemy", False)
        status_evts = [e for e in events if e.event_type == "status_applied" and e.status == "tox"]
        assert len(status_evts) == 1
        assert defender.status == "tox"

    def test_toxic_respects_poison_type_immunity(self):
        attacker = _make_pokemon(name="Attacker")
        defender = _make_pokemon(name="Defender", types=["poison"])
        with patch("backend.services.status_service.random") as mock_random:
            mock_random.randint.return_value = 1
            events = process_move_effects("Toxic", attacker, defender, "player", "enemy", False)
        assert defender.status is None

    def test_toxic_respects_steel_type_immunity(self):
        attacker = _make_pokemon(name="Attacker")
        defender = _make_pokemon(name="Defender", types=["steel"])
        with patch("backend.services.status_service.random") as mock_random:
            mock_random.randint.return_value = 1
            events = process_move_effects("Toxic", attacker, defender, "player", "enemy", False)
        assert defender.status is None


# ============================================================
# BE-02: Confuse Ray inflicts confusion
# ============================================================

class TestConfuseRay:
    def test_confuse_ray_applies_confusion(self):
        attacker = _make_pokemon(name="Attacker")
        defender = _make_pokemon(name="Defender")
        with patch("backend.services.status_service.random") as mock_random:
            mock_random.randint.side_effect = [1, 3]  # hits 100% chance, then confusion turns=3
            events = process_move_effects("Confuse Ray", attacker, defender, "player", "enemy", False)
        assert defender.confused is True
        assert 2 <= defender.confused_turns <= 5
        confusion_evts = [e for e in events if e.status == "confusion"]
        assert len(confusion_evts) == 1

    def test_confuse_ray_no_double_confusion(self):
        attacker = _make_pokemon(name="Attacker")
        defender = _make_pokemon(name="Defender", confused=True, confused_turns=3)
        with patch("backend.services.status_service.random") as mock_random:
            mock_random.randint.return_value = 1
            events = process_move_effects("Confuse Ray", attacker, defender, "player", "enemy", False)
        confusion_evts = [e for e in events if e.status == "confusion"]
        assert len(confusion_evts) == 0


# ============================================================
# BE-02: Flinch moves (Bite, Headbutt)
# ============================================================

class TestFlinchMoves:
    def test_bite_can_flinch(self):
        attacker = _make_pokemon(name="Attacker")
        defender = _make_pokemon(name="Defender")
        with patch("backend.services.status_service.random") as mock_random:
            mock_random.randint.return_value = 1  # always hits flinch chance
            events = process_move_effects("Bite", attacker, defender, "player", "enemy", True)
        assert defender.flinched is True
        flinch_evts = [e for e in events if e.status == "flinch"]
        assert len(flinch_evts) == 1

    def test_headbutt_can_flinch(self):
        attacker = _make_pokemon(name="Attacker")
        defender = _make_pokemon(name="Defender")
        with patch("backend.services.status_service.random") as mock_random:
            mock_random.randint.return_value = 1
            events = process_move_effects("Headbutt", attacker, defender, "player", "enemy", True)
        assert defender.flinched is True

    def test_flinch_requires_damage(self):
        attacker = _make_pokemon(name="Attacker")
        defender = _make_pokemon(name="Defender")
        with patch("backend.services.status_service.random") as mock_random:
            mock_random.randint.return_value = 1
            events = process_move_effects("Bite", attacker, defender, "player", "enemy", False)
        assert defender.flinched is False

    def test_flinch_prevents_move(self):
        pokemon = _make_pokemon(name="TestMon", flinched=True)
        can_move, events = process_status_before_move(pokemon, "player")
        assert can_move is False
        assert any(e.status == "flinch" for e in events)


# ============================================================
# BE-05: Water Veil prevents burns
# ============================================================

class TestWaterVeil:
    def test_water_veil_prevents_burn(self):
        pokemon = _make_pokemon(ability_id="water_veil")
        assert ability_prevents_status(pokemon, "brn") is True

    def test_water_veil_does_not_prevent_paralysis(self):
        pokemon = _make_pokemon(ability_id="water_veil")
        assert ability_prevents_status(pokemon, "par") is False

    def test_water_veil_burn_application_blocked(self):
        pokemon = _make_pokemon(name="Vaporeon", ability_id="water_veil")
        evt = apply_status(pokemon, "brn", "player")
        assert pokemon.status is None
        assert evt is not None
        assert evt.event_type == "status_prevented"


# ============================================================
# Wonder Guard: blocks non-super-effective damage
# ============================================================

class TestWonderGuard:
    def test_wonder_guard_blocks_neutral_move(self):
        defender = _make_pokemon(name="Shedinja", types=["bug", "ghost"], ability_id="wonder_guard")
        move = _make_move(name="Tackle", type="normal", power=40)
        immune, events = check_ability_type_immunity(defender, move, "enemy")
        assert immune is True
        assert any("Wonder Guard" in e.message for e in events)

    def test_wonder_guard_blocks_not_very_effective(self):
        defender = _make_pokemon(name="Shedinja", types=["bug", "ghost"], ability_id="wonder_guard")
        move = _make_move(name="Poison Sting", type="poison", power=15)
        immune, events = check_ability_type_immunity(defender, move, "enemy")
        assert immune is True

    def test_wonder_guard_allows_super_effective(self):
        defender = _make_pokemon(name="Shedinja", types=["bug", "ghost"], ability_id="wonder_guard")
        move = _make_move(name="Flamethrower", type="fire", power=90)
        immune, events = check_ability_type_immunity(defender, move, "enemy")
        assert immune is False

    def test_wonder_guard_ignores_status_moves(self):
        defender = _make_pokemon(name="Shedinja", types=["bug", "ghost"], ability_id="wonder_guard")
        move = _make_move(name="Growl", type="normal", power=0)
        immune, events = check_ability_type_immunity(defender, move, "enemy")
        assert immune is False

    def test_wonder_guard_blocks_immune_type(self):
        """Normal is immune to ghost — effectiveness is 0.0 which is <= 1.0, so Wonder Guard blocks."""
        defender = _make_pokemon(name="Shedinja", types=["bug", "ghost"], ability_id="wonder_guard")
        move = _make_move(name="Tackle", type="normal", power=40)
        immune, events = check_ability_type_immunity(defender, move, "enemy")
        assert immune is True


# ============================================================
# Moxie: +1 Attack on KO
# ============================================================

class TestMoxie:
    def test_moxie_boosts_attack_on_ko(self):
        attacker = _make_pokemon(name="Gyarados", ability_id="moxie")
        events = process_ability_on_ko(attacker, "player")
        assert len(events) >= 2  # ability_activated + stat_change
        assert attacker.stat_stages.attack == 1

    def test_moxie_stacks(self):
        attacker = _make_pokemon(name="Gyarados", ability_id="moxie")
        process_ability_on_ko(attacker, "player")
        process_ability_on_ko(attacker, "player")
        assert attacker.stat_stages.attack == 2

    def test_moxie_no_trigger_when_fainted(self):
        attacker = _make_pokemon(name="Gyarados", ability_id="moxie", current_hp=0)
        events = process_ability_on_ko(attacker, "player")
        assert len(events) == 0

    def test_moxie_no_trigger_without_ability(self):
        attacker = _make_pokemon(name="Gyarados")
        events = process_ability_on_ko(attacker, "player")
        assert len(events) == 0
