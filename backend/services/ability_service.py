"""Pokemon abilities system - registry, triggers, and battle integration."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

from ..models.battle import BattlePokemon, BattleState, StatusEvent
from ..models.pokemon import Move
from ..models.weather import WeatherEvent

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_abilities_db: dict[str, dict] = {}


def _load_abilities() -> None:
    global _abilities_db
    with open(DATA_DIR / "abilities.json") as f:
        _abilities_db = json.load(f)


def get_ability(ability_id: str) -> Optional[dict]:
    if not _abilities_db:
        _load_abilities()
    return _abilities_db.get(ability_id)


def get_ability_name(ability_id: str) -> str:
    ab = get_ability(ability_id)
    return ab["name"] if ab else ability_id


def select_ability(abilities: list[str]) -> Optional[str]:
    """Randomly select an ability from a species' ability pool."""
    if not abilities:
        return None
    return random.choice(abilities)


# --- Ability event helpers ---

def _ability_event(
    pokemon: BattlePokemon,
    role: str,
    event_type: str,
    message: str,
    **kwargs,
) -> StatusEvent:
    ab = get_ability(pokemon.ability_id) if pokemon.ability_id else None
    return StatusEvent(
        pokemon=role,
        event_type=event_type,
        message=message,
        ability_id=pokemon.ability_id,
        ability_name=ab["name"] if ab else None,
        **kwargs,
    )


# --- Switch-in abilities ---

def process_switch_in_ability(
    pokemon: BattlePokemon,
    opponent: BattlePokemon,
    role: str,
    opponent_role: str,
) -> list[StatusEvent]:
    """Process abilities that trigger when a Pokemon enters battle."""
    if not pokemon.ability_id:
        return []

    events = []
    ab = get_ability(pokemon.ability_id)
    if not ab:
        return []

    if pokemon.ability_id == "intimidate":
        from .status_service import apply_stat_change
        evt = apply_stat_change(opponent, "attack", -1, opponent_role)
        if evt:
            evt.ability_id = pokemon.ability_id
            evt.ability_name = ab["name"]
            events.append(_ability_event(
                pokemon, role, "ability_activated",
                f"{pokemon.name}'s Intimidate lowered {opponent.name}'s Attack!",
            ))
            events.append(evt)

    return events


# --- Damage modification abilities ---

def process_ability_damage_modifier(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move: Move,
    damage: int,
    attacker_role: str,
    defender_role: str,
) -> tuple[int, list[StatusEvent]]:
    """Modify damage based on abilities. Returns (modified_damage, events)."""
    events = []

    # Attacker abilities: Overgrow/Blaze/Torrent
    if attacker.ability_id in ("overgrow", "blaze", "torrent"):
        ab = get_ability(attacker.ability_id)
        td = ab["trigger_data"]
        if move.type == td["move_type"] and attacker.current_hp <= attacker.max_hp * td["hp_threshold"]:
            damage = int(damage * td["boost"])
            events.append(_ability_event(
                attacker, attacker_role, "ability_activated",
                f"{attacker.name}'s {ab['name']} boosted its {move.type}-type move!",
            ))

    # Flash Fire boost (attacker has activated flash fire)
    if attacker.ability_id == "flash_fire" and attacker.flash_fire_activated and move.type == "fire":
        damage = int(damage * 1.5)
        events.append(_ability_event(
            attacker, attacker_role, "ability_activated",
            f"{attacker.name}'s Flash Fire boosted its fire-type move!",
        ))

    # Defender abilities: Sturdy
    if defender.ability_id == "sturdy" and defender.current_hp == defender.max_hp and damage >= defender.current_hp:
        damage = defender.current_hp - 1
        events.append(_ability_event(
            defender, defender_role, "ability_activated",
            f"{defender.name} endured the hit with Sturdy!",
        ))

    return damage, events


def check_ability_type_immunity(
    defender: BattlePokemon,
    move: Move,
    defender_role: str,
) -> tuple[bool, list[StatusEvent]]:
    """Check if defender's ability grants immunity to the move type.

    Returns (is_immune, events). If immune, the caller should skip damage.
    """
    if not defender.ability_id:
        return False, []

    events = []

    # Levitate: immune to ground
    if defender.ability_id == "levitate" and move.type == "ground" and move.power > 0:
        events.append(_ability_event(
            defender, defender_role, "ability_activated",
            f"{defender.name}'s Levitate makes it immune to Ground moves!",
        ))
        return True, events

    # Water Absorb: heal from water moves
    if defender.ability_id == "water_absorb" and move.type == "water" and move.power > 0:
        heal = max(1, defender.max_hp // 4)
        actual_heal = min(heal, defender.max_hp - defender.current_hp)
        if actual_heal > 0:
            defender.current_hp += actual_heal
        events.append(_ability_event(
            defender, defender_role, "ability_activated",
            f"{defender.name}'s Water Absorb restored its HP!",
        ))
        return True, events

    # Flash Fire: immune to fire, activate boost
    if defender.ability_id == "flash_fire" and move.type == "fire" and move.power > 0:
        defender.flash_fire_activated = True
        events.append(_ability_event(
            defender, defender_role, "ability_activated",
            f"{defender.name}'s Flash Fire absorbed the fire move!",
        ))
        return True, events

    return False, events


# --- On-hit abilities (contact-based) ---

def process_ability_on_hit(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move: Move,
    attacker_role: str,
    defender_role: str,
) -> list[StatusEvent]:
    """Process abilities that trigger when the defender is hit (e.g. Static, Flame Body)."""
    if not defender.ability_id:
        return []

    # Only trigger on contact moves
    is_contact = getattr(move, "contact", False)
    if not is_contact:
        # Also check move data for contact flag
        from .encounter_service import get_move_data
        md = get_move_data(move.name)
        if not md or not md.get("contact", False):
            return []

    events = []
    ab = get_ability(defender.ability_id)
    if not ab or "on_hit" not in ab.get("trigger_types", []):
        return []

    td = ab["trigger_data"]
    if not td.get("contact_only", False) or is_contact or (get_move_data(move.name) or {}).get("contact", False):
        if random.random() < td.get("chance", 0):
            status = td.get("status")
            if status:
                from .status_service import apply_status
                evt = apply_status(attacker, status, attacker_role)
                if evt:
                    events.append(_ability_event(
                        defender, defender_role, "ability_activated",
                        f"{defender.name}'s {ab['name']} affected {attacker.name}!",
                    ))
                    events.append(evt)

    return events


# --- End-of-turn abilities ---

def process_ability_end_of_turn(
    pokemon: BattlePokemon,
    role: str,
) -> list[StatusEvent]:
    """Process abilities that trigger at end of turn."""
    if not pokemon.ability_id or pokemon.current_hp <= 0:
        return []

    events = []

    # Speed Boost
    if pokemon.ability_id == "speed_boost":
        from .status_service import apply_stat_change
        evt = apply_stat_change(pokemon, "speed", 1, role)
        if evt:
            events.append(_ability_event(
                pokemon, role, "ability_activated",
                f"{pokemon.name}'s Speed Boost raised its Speed!",
            ))
            events.append(evt)

    return events


# --- Status immunity abilities ---

def ability_prevents_status(pokemon: BattlePokemon, status: str) -> bool:
    """Check if a Pokemon's ability prevents a status condition."""
    if not pokemon.ability_id:
        return False

    if pokemon.ability_id == "limber" and status == "par":
        return True

    return False


# --- Stat change prevention abilities ---

def ability_prevents_stat_drop(pokemon: BattlePokemon, stat: str) -> bool:
    """Check if a Pokemon's ability prevents a stat reduction."""
    if not pokemon.ability_id:
        return False

    if pokemon.ability_id == "keen_eye" and stat == "accuracy":
        return True

    return False


# --- Weather abilities ---

_WEATHER_ABILITIES: dict[str, str] = {
    "drizzle": "rain",
    "drought": "sun",
    "sand_stream": "sandstorm",
    "snow_warning": "hail",
}

_WEATHER_SPEED_ABILITIES: dict[str, str] = {
    "swift_swim": "rain",
    "chlorophyll": "sun",
    "sand_rush": "sandstorm",
}


def process_weather_ability_on_switch_in(
    pokemon: BattlePokemon,
    role: str,
    battle: BattleState,
) -> list[WeatherEvent]:
    """Process weather-setting abilities on switch-in (Drizzle, Drought, etc.)."""
    if not pokemon.ability_id:
        return []

    weather = _WEATHER_ABILITIES.get(pokemon.ability_id)
    if weather is None:
        return []

    from .weather_service import set_weather
    evt = set_weather(battle, weather, duration=0)  # indefinite
    ab = get_ability(pokemon.ability_id)
    ab_name = ab["name"] if ab else pokemon.ability_id
    evt.message = f"{pokemon.name}'s {ab_name} set the weather to {evt.message.split('!')[0].split(' ')[-1]}!"
    return [evt]


def get_weather_speed_multiplier(pokemon: BattlePokemon, weather: str | None) -> float:
    """Get speed multiplier from weather-speed abilities (Swift Swim, Chlorophyll, Sand Rush)."""
    if not pokemon.ability_id or weather is None:
        return 1.0

    required_weather = _WEATHER_SPEED_ABILITIES.get(pokemon.ability_id)
    if required_weather and required_weather == weather:
        return 2.0

    return 1.0


def process_ability_weather_end_of_turn(
    pokemon: BattlePokemon,
    role: str,
    weather: str | None,
) -> list[WeatherEvent]:
    """Process weather-related end-of-turn abilities (Rain Dish, etc.)."""
    if not pokemon.ability_id or pokemon.current_hp <= 0 or weather is None:
        return []

    events: list[WeatherEvent] = []

    # Rain Dish: heal 1/16 HP in rain
    if pokemon.ability_id == "rain_dish" and weather == "rain":
        if pokemon.current_hp < pokemon.max_hp:
            heal = max(1, pokemon.max_hp // 16)
            actual = min(heal, pokemon.max_hp - pokemon.current_hp)
            pokemon.current_hp += actual
            ab = get_ability(pokemon.ability_id)
            ab_name = ab["name"] if ab else "Rain Dish"
            events.append(WeatherEvent(
                event_type="weather_heal",
                weather="rain",
                pokemon=role,
                damage=-actual,
                message=f"{pokemon.name}'s {ab_name} restored a little HP!",
            ))

    return events
