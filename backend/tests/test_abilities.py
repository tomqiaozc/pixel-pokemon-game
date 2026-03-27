"""Tests for the Pokemon abilities system."""
from __future__ import annotations

from unittest.mock import patch

from backend.models.battle import BattlePokemon, StatStages
from backend.models.pokemon import Move, Stats
from backend.services.ability_service import (
    check_ability_type_immunity,
    get_ability,
    process_ability_damage_modifier,
    process_ability_end_of_turn,
    process_ability_on_hit,
    process_switch_in_ability,
    select_ability,
)
from backend.services.battle_service import start_battle, process_action
from backend.services.encounter_service import generate_wild_pokemon
from backend.services.status_service import apply_stat_change, apply_status, can_apply_status


def _make_pokemon(
    name="Charmander",
    types=None,
    ability_id=None,
    hp=100,
    level=10,
) -> BattlePokemon:
    if types is None:
        types = ["fire"]
    return BattlePokemon(
        species_id=4,
        name=name,
        types=types,
        level=level,
        stats=Stats(hp=hp, attack=50, defense=50, sp_attack=50, sp_defense=50, speed=50),
        current_hp=hp,
        max_hp=hp,
        moves=[Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35, contact=True)],
        sprite="test.png",
        ability_id=ability_id,
    )


# --- Ability Registry Tests ---

def test_get_ability():
    ab = get_ability("overgrow")
    assert ab is not None
    assert ab["name"] == "Overgrow"
    assert "before_damage" in ab["trigger_types"]


def test_get_ability_not_found():
    assert get_ability("nonexistent") is None


def test_select_ability_from_list():
    result = select_ability(["overgrow"])
    assert result == "overgrow"


def test_select_ability_empty():
    assert select_ability([]) is None


# --- Overgrow/Blaze/Torrent Tests ---

def test_overgrow_boosts_grass_move_at_low_hp():
    attacker = _make_pokemon(name="Bulbasaur", types=["grass"], ability_id="overgrow", hp=100)
    defender = _make_pokemon(name="Pidgey", types=["normal"])
    attacker.current_hp = 30  # 30% < 33% threshold

    grass_move = Move(name="Vine Whip", type="grass", power=45, accuracy=100, pp=25, contact=True)
    dmg, events = process_ability_damage_modifier(attacker, defender, grass_move, 50, "player", "enemy")
    assert dmg == 75  # 50 * 1.5
    assert len(events) == 1
    assert "Overgrow" in events[0].message


def test_overgrow_no_boost_at_high_hp():
    attacker = _make_pokemon(name="Bulbasaur", types=["grass"], ability_id="overgrow", hp=100)
    defender = _make_pokemon(name="Pidgey", types=["normal"])
    attacker.current_hp = 80  # 80% > 33%

    grass_move = Move(name="Vine Whip", type="grass", power=45, accuracy=100, pp=25, contact=True)
    dmg, events = process_ability_damage_modifier(attacker, defender, grass_move, 50, "player", "enemy")
    assert dmg == 50
    assert len(events) == 0


def test_blaze_boosts_fire_move():
    attacker = _make_pokemon(ability_id="blaze", hp=100)
    defender = _make_pokemon(name="Pidgey", types=["normal"])
    attacker.current_hp = 20

    fire_move = Move(name="Ember", type="fire", power=40, accuracy=100, pp=25)
    dmg, events = process_ability_damage_modifier(attacker, defender, fire_move, 40, "player", "enemy")
    assert dmg == 60  # 40 * 1.5
    assert len(events) == 1


def test_torrent_boosts_water_move():
    attacker = _make_pokemon(name="Squirtle", types=["water"], ability_id="torrent", hp=100)
    defender = _make_pokemon(name="Pidgey", types=["normal"])
    attacker.current_hp = 25

    water_move = Move(name="Water Gun", type="water", power=40, accuracy=100, pp=25)
    dmg, events = process_ability_damage_modifier(attacker, defender, water_move, 60, "player", "enemy")
    assert dmg == 90  # 60 * 1.5


# --- Sturdy Tests ---

def test_sturdy_prevents_ohko():
    attacker = _make_pokemon(name="Attacker", types=["normal"])
    defender = _make_pokemon(name="Geodude", types=["rock"], ability_id="sturdy", hp=50)
    defender.current_hp = 50  # full HP

    dmg, events = process_ability_damage_modifier(attacker, defender, Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35, contact=True), 999, "player", "enemy")
    assert dmg == 49  # survives with 1 HP
    assert any("Sturdy" in e.message for e in events)


def test_sturdy_no_effect_not_full_hp():
    attacker = _make_pokemon(name="Attacker", types=["normal"])
    defender = _make_pokemon(name="Geodude", types=["rock"], ability_id="sturdy", hp=50)
    defender.current_hp = 30  # not full HP

    dmg, events = process_ability_damage_modifier(attacker, defender, Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35, contact=True), 999, "player", "enemy")
    assert dmg == 999  # no protection
    assert len(events) == 0


# --- Levitate Tests ---

def test_levitate_immune_to_ground():
    defender = _make_pokemon(name="Gengar", types=["ghost", "poison"], ability_id="levitate")
    ground_move = Move(name="Earthquake", type="ground", power=100, accuracy=100, pp=10)

    immune, events = check_ability_type_immunity(defender, ground_move, "enemy")
    assert immune is True
    assert len(events) == 1
    assert "Levitate" in events[0].message


def test_levitate_not_immune_to_other_types():
    defender = _make_pokemon(name="Gengar", types=["ghost"], ability_id="levitate")
    fire_move = Move(name="Ember", type="fire", power=40, accuracy=100, pp=25)

    immune, events = check_ability_type_immunity(defender, fire_move, "enemy")
    assert immune is False


# --- Water Absorb Tests ---

def test_water_absorb_heals():
    defender = _make_pokemon(name="Staryu", types=["water"], ability_id="water_absorb", hp=100)
    defender.current_hp = 50
    water_move = Move(name="Water Gun", type="water", power=40, accuracy=100, pp=25)

    immune, events = check_ability_type_immunity(defender, water_move, "enemy")
    assert immune is True
    assert defender.current_hp == 75  # healed 25%
    assert any("Water Absorb" in e.message for e in events)


# --- Flash Fire Tests ---

def test_flash_fire_immunity_and_boost():
    defender = _make_pokemon(name="Flareon", types=["fire"], ability_id="flash_fire", hp=100)
    fire_move = Move(name="Ember", type="fire", power=40, accuracy=100, pp=25)

    immune, events = check_ability_type_immunity(defender, fire_move, "enemy")
    assert immune is True
    assert defender.flash_fire_activated is True
    assert any("Flash Fire" in e.message for e in events)


def test_flash_fire_boosts_own_fire_move():
    attacker = _make_pokemon(name="Flareon", types=["fire"], ability_id="flash_fire", hp=100)
    attacker.flash_fire_activated = True
    defender = _make_pokemon(name="Pidgey", types=["normal"])

    fire_move = Move(name="Ember", type="fire", power=40, accuracy=100, pp=25)
    dmg, events = process_ability_damage_modifier(attacker, defender, fire_move, 60, "player", "enemy")
    assert dmg == 90  # 60 * 1.5


# --- Static/Flame Body/Poison Point Tests ---

def test_static_paralyzes_on_contact():
    attacker = _make_pokemon(name="Attacker", types=["normal"])
    defender = _make_pokemon(name="Pikachu", types=["electric"], ability_id="static")
    contact_move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35, contact=True)

    with patch("backend.services.ability_service.random.random", return_value=0.1):
        events = process_ability_on_hit(attacker, defender, contact_move, "player", "enemy")

    assert len(events) >= 1
    # Should have paralysis applied
    assert attacker.status == "par"


def test_static_no_trigger_on_non_contact():
    attacker = _make_pokemon(name="Attacker", types=["normal"])
    defender = _make_pokemon(name="Pikachu", types=["electric"], ability_id="static")
    non_contact_move = Move(name="Gust", type="flying", power=40, accuracy=100, pp=35, contact=False)

    with patch("backend.services.ability_service.random.random", return_value=0.1):
        events = process_ability_on_hit(attacker, defender, non_contact_move, "player", "enemy")

    assert len(events) == 0
    assert attacker.status is None


# --- Intimidate Tests ---

def test_intimidate_lowers_attack():
    pokemon = _make_pokemon(name="Gyarados", types=["water", "flying"], ability_id="intimidate")
    opponent = _make_pokemon(name="Pidgey", types=["normal"])

    events = process_switch_in_ability(pokemon, opponent, "player", "enemy")
    assert len(events) >= 1
    assert opponent.stat_stages.attack == -1


# --- Speed Boost Tests ---

def test_speed_boost_raises_speed():
    pokemon = _make_pokemon(name="Ninjask", types=["bug"], ability_id="speed_boost")

    events = process_ability_end_of_turn(pokemon, "player")
    assert len(events) >= 1
    assert pokemon.stat_stages.speed == 1


# --- Limber Tests ---

def test_limber_prevents_paralysis():
    pokemon = _make_pokemon(name="Persian", types=["normal"], ability_id="limber")
    assert can_apply_status(pokemon, "par") is False

    evt = apply_status(pokemon, "par", "player")
    assert evt is not None
    assert evt.event_type == "status_prevented"
    assert "Limber" in evt.message


# --- Keen Eye Tests ---

def test_keen_eye_prevents_accuracy_drop():
    pokemon = _make_pokemon(name="Pidgey", types=["normal", "flying"], ability_id="keen_eye")

    evt = apply_stat_change(pokemon, "accuracy", -1, "player")
    assert evt is not None
    assert evt.stages == 0
    assert "Keen Eye" in evt.message
    assert pokemon.stat_stages.accuracy == 0  # unchanged


def test_keen_eye_allows_accuracy_boost():
    pokemon = _make_pokemon(name="Pidgey", types=["normal", "flying"], ability_id="keen_eye")

    evt = apply_stat_change(pokemon, "accuracy", 1, "player")
    assert evt is not None
    assert pokemon.stat_stages.accuracy == 1  # allowed


# --- Wild Pokemon Generation Tests ---

def test_wild_pokemon_has_ability():
    wild = generate_wild_pokemon(15, 10)  # Pikachu
    assert wild.ability_id == "static"


def test_wild_pokemon_random_ability():
    # Geodude has two abilities: rock_head, sturdy
    abilities_seen = set()
    for _ in range(50):
        wild = generate_wild_pokemon(17, 5)
        abilities_seen.add(wild.ability_id)
    assert "rock_head" in abilities_seen or "sturdy" in abilities_seen


# --- Battle Integration Test ---

def test_battle_with_abilities():
    """Test that abilities are preserved through battle creation."""
    battle = start_battle(
        player_pokemon_data={
            "species_id": 4, "name": "Charmander", "types": ["fire"], "level": 5,
            "stats": {"hp": 35, "attack": 30, "defense": 25, "sp_attack": 35, "sp_defense": 30, "speed": 40},
            "current_hp": 35, "max_hp": 35,
            "moves": [{"name": "Scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35, "contact": True}],
            "sprite": "charmander.png",
            "ability_id": "blaze",
        },
        enemy_pokemon_data={
            "species_id": 15, "name": "Pikachu", "types": ["electric"], "level": 5,
            "stats": {"hp": 35, "attack": 30, "defense": 25, "sp_attack": 35, "sp_defense": 30, "speed": 40},
            "current_hp": 35, "max_hp": 35,
            "moves": [{"name": "Thunder Shock", "type": "electric", "power": 40, "accuracy": 100, "pp": 30}],
            "sprite": "pikachu.png",
            "ability_id": "static",
        },
    )
    assert battle.player_pokemon.ability_id == "blaze"
    assert battle.enemy_pokemon.ability_id == "static"
