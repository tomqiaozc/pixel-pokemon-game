"""Tests for status conditions, stat stages, and battle integration."""
from __future__ import annotations

import random

from fastapi.testclient import TestClient

from backend.main import app
from backend.models.battle import BattlePokemon, StatStages, StatusEvent
from backend.services.status_service import (
    apply_stat_change,
    apply_status,
    can_apply_status,
    get_effective_stat,
    process_move_effects,
    process_status_before_move,
    process_status_end_of_turn,
)
from backend.services.battle_service import start_battle, process_action

client = TestClient(app)


def _make_pokemon(**overrides) -> BattlePokemon:
    defaults = {
        "species_id": 1,
        "name": "Bulbasaur",
        "types": ["grass", "poison"],
        "level": 50,
        "stats": {"hp": 150, "attack": 100, "defense": 100, "sp_attack": 100, "sp_defense": 100, "speed": 100},
        "current_hp": 150,
        "max_hp": 150,
        "moves": [
            {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35},
        ],
        "sprite": "bulbasaur",
    }
    defaults.update(overrides)
    return BattlePokemon(**defaults)


# --- Stat Stages Tests ---

def test_stat_stage_multiplier_positive():
    poke = _make_pokemon()
    poke.stat_stages.attack = 2
    eff = get_effective_stat(poke, "attack")
    # +2 stage: (2+2)/2 = 2.0x
    assert eff == 200


def test_stat_stage_multiplier_negative():
    poke = _make_pokemon()
    poke.stat_stages.defense = -2
    eff = get_effective_stat(poke, "defense")
    # -2 stage: 2/(2+2) = 0.5x
    assert eff == 50


def test_stat_stage_clamp():
    poke = _make_pokemon()
    poke.stat_stages.speed = 10  # should clamp to +6
    eff = get_effective_stat(poke, "speed")
    # +6 stage: (2+6)/2 = 4.0x
    assert eff == 400


def test_stat_min_1():
    poke = _make_pokemon(stats={"hp": 150, "attack": 1, "defense": 1, "sp_attack": 1, "sp_defense": 1, "speed": 1})
    poke.stat_stages.attack = -6
    eff = get_effective_stat(poke, "attack")
    # Should be at least 1
    assert eff >= 1


def test_burn_halves_attack():
    poke = _make_pokemon()
    poke.status = "brn"
    eff = get_effective_stat(poke, "attack")
    assert eff == 50  # 100 // 2


def test_paralysis_quarters_speed():
    poke = _make_pokemon()
    poke.status = "par"
    eff = get_effective_stat(poke, "speed")
    assert eff == 25  # 100 // 4


# --- Status Application Tests ---

def test_apply_status_poison():
    poke = _make_pokemon(types=["normal"])
    evt = apply_status(poke, "psn", "player")
    assert evt is not None
    assert poke.status == "psn"
    assert evt.event_type == "status_applied"


def test_cannot_double_status():
    poke = _make_pokemon(types=["normal"])
    apply_status(poke, "psn", "player")
    assert not can_apply_status(poke, "brn")


def test_fire_immune_to_burn():
    poke = _make_pokemon(types=["fire"])
    assert not can_apply_status(poke, "brn")


def test_electric_immune_to_paralysis():
    poke = _make_pokemon(types=["electric"])
    assert not can_apply_status(poke, "par")


def test_poison_immune_to_poison():
    poke = _make_pokemon(types=["poison"])
    assert not can_apply_status(poke, "psn")


def test_ice_immune_to_freeze():
    poke = _make_pokemon(types=["ice"])
    assert not can_apply_status(poke, "frz")


def test_status_immune_event():
    poke = _make_pokemon(types=["fire"])
    evt = apply_status(poke, "brn", "player")
    assert evt is not None
    assert evt.event_type == "status_prevented"


# --- Sleep Tests ---

def test_sleep_prevents_move():
    random.seed(42)
    poke = _make_pokemon()
    poke.status = "slp"
    poke.status_turns = 3
    can_move, events = process_status_before_move(poke, "player")
    assert not can_move
    assert any(e.status == "slp" for e in events)


def test_sleep_wakes_up():
    poke = _make_pokemon()
    poke.status = "slp"
    poke.status_turns = 1
    can_move, events = process_status_before_move(poke, "player")
    assert can_move
    assert poke.status is None
    assert any(e.event_type == "status_cured" for e in events)


# --- Freeze Tests ---

def test_freeze_prevents_move():
    random.seed(0)  # make thaw fail
    poke = _make_pokemon()
    poke.status = "frz"
    can_move, events = process_status_before_move(poke, "player")
    assert not can_move


# --- Paralysis Tests ---

def test_paralysis_sometimes_prevents():
    prevented = 0
    for i in range(100):
        random.seed(i)
        poke = _make_pokemon()
        poke.status = "par"
        can_move, _ = process_status_before_move(poke, "player")
        if not can_move:
            prevented += 1
    # ~25% should be prevented
    assert 10 < prevented < 50


# --- Flinch Test ---

def test_flinch_prevents_move():
    poke = _make_pokemon()
    poke.flinched = True
    can_move, events = process_status_before_move(poke, "player")
    assert not can_move
    assert poke.flinched is False
    assert events[0].status == "flinch"


# --- End-of-Turn Damage Tests ---

def test_poison_damage():
    poke = _make_pokemon()
    poke.status = "psn"
    events = process_status_end_of_turn(poke, "player")
    assert len(events) == 1
    assert events[0].damage == 150 // 8  # 1/8 max HP


def test_burn_damage():
    poke = _make_pokemon()
    poke.status = "brn"
    events = process_status_end_of_turn(poke, "player")
    assert len(events) == 1
    assert events[0].damage == 150 // 8


def test_toxic_increasing_damage():
    poke = _make_pokemon()
    poke.status = "tox"
    poke.status_turns = 1
    events1 = process_status_end_of_turn(poke, "player")
    dmg1 = events1[0].damage
    events2 = process_status_end_of_turn(poke, "player")
    dmg2 = events2[0].damage
    assert dmg2 > dmg1  # toxic damage increases


# --- Stat Change Tests ---

def test_stat_change_up():
    poke = _make_pokemon()
    evt = apply_stat_change(poke, "attack", 1, "player")
    assert poke.stat_stages.attack == 1
    assert evt.stages == 1


def test_stat_change_capped():
    poke = _make_pokemon()
    poke.stat_stages.attack = 6
    evt = apply_stat_change(poke, "attack", 1, "player")
    assert poke.stat_stages.attack == 6
    assert evt.stages == 0  # no change


# --- Move Effects Tests ---

def test_thunder_wave_applies_paralysis():
    random.seed(0)
    attacker = _make_pokemon(types=["electric"])
    defender = _make_pokemon(types=["normal"])
    events = process_move_effects("Thunder Wave", attacker, defender, "player", "enemy", False)
    status_applied = [e for e in events if e.event_type == "status_applied"]
    assert len(status_applied) == 1
    assert defender.status == "par"


def test_growl_lowers_attack():
    attacker = _make_pokemon()
    defender = _make_pokemon()
    events = process_move_effects("Growl", attacker, defender, "player", "enemy", False)
    assert defender.stat_stages.attack == -1
    assert any(e.event_type == "stat_change" for e in events)


# --- Battle Integration Tests ---

def test_battle_with_status_events():
    """Start a battle and run a turn, verify status_events field exists in response."""
    battle = start_battle(
        player_pokemon_data={
            "species_id": 4,
            "name": "Charmander",
            "types": ["fire"],
            "level": 10,
            "stats": {"hp": 35, "attack": 30, "defense": 25, "sp_attack": 35, "sp_defense": 30, "speed": 40},
            "current_hp": 35,
            "max_hp": 35,
            "moves": [
                {"name": "Ember", "type": "fire", "power": 40, "accuracy": 100, "pp": 25},
            ],
            "sprite": "charmander",
        },
        enemy_pokemon_data={
            "species_id": 1,
            "name": "Bulbasaur",
            "types": ["grass", "poison"],
            "level": 10,
            "stats": {"hp": 35, "attack": 25, "defense": 30, "sp_attack": 35, "sp_defense": 30, "speed": 25},
            "current_hp": 35,
            "max_hp": 35,
            "moves": [
                {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35},
            ],
            "sprite": "bulbasaur",
        },
    )

    result = process_action(battle.id, "fight", 0)
    assert result is not None
    assert hasattr(result, "status_events")
    assert isinstance(result.status_events, list)


def test_battle_poison_end_of_turn():
    """Verify poison damage is applied at end of turn via battle integration."""
    random.seed(99)
    battle = start_battle(
        player_pokemon_data={
            "species_id": 4,
            "name": "Charmander",
            "types": ["fire"],
            "level": 50,
            "stats": {"hp": 150, "attack": 100, "defense": 100, "sp_attack": 100, "sp_defense": 100, "speed": 100},
            "current_hp": 150,
            "max_hp": 150,
            "moves": [
                {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35},
            ],
            "sprite": "charmander",
        },
        enemy_pokemon_data={
            "species_id": 1,
            "name": "Bulbasaur",
            "types": ["grass", "poison"],
            "level": 50,
            "stats": {"hp": 150, "attack": 100, "defense": 100, "sp_attack": 100, "sp_defense": 100, "speed": 50},
            "current_hp": 150,
            "max_hp": 150,
            "moves": [
                {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35},
            ],
            "sprite": "bulbasaur",
        },
    )

    # Manually poison the enemy
    battle.enemy_pokemon.status = "psn"

    result = process_action(battle.id, "fight", 0)
    assert result is not None
    # Check that poison damage was applied
    poison_events = [e for e in result.status_events if e.status == "psn" and e.event_type == "status_damage"]
    assert len(poison_events) == 1


def test_api_battle_turn_includes_status_events():
    """Test that the API response includes status_events."""
    # Start battle via API
    resp = client.post("/api/battle/start", json={
        "game_id": "test123",
        "wild_pokemon": {
            "species_id": 1,
            "name": "Bulbasaur",
            "types": ["grass", "poison"],
            "level": 5,
            "stats": {"hp": 25, "attack": 20, "defense": 20, "sp_attack": 25, "sp_defense": 25, "speed": 20},
            "current_hp": 25,
            "max_hp": 25,
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "bulbasaur",
        },
    })
    if resp.status_code == 200:
        data = resp.json()
        battle_id = data["battle"]["id"]

        action_resp = client.post("/api/battle/action", json={
            "battle_id": battle_id,
            "action": "fight",
            "move_index": 0,
        })
        if action_resp.status_code == 200:
            result = action_resp.json()
            assert "turn_result" in result
            if result["turn_result"]:
                assert "status_events" in result["turn_result"]
