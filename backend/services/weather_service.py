"""Weather system – state management, damage, and move/type modifiers."""
from __future__ import annotations

from ..models.battle import BattlePokemon, BattleState
from ..models.weather import WeatherEvent, WeatherState

# Weather names for display messages
_WEATHER_NAMES: dict[str, str] = {
    "rain": "Rain",
    "sun": "Harsh Sunlight",
    "sandstorm": "Sandstorm",
    "hail": "Hail",
}

# Move-type damage multipliers per weather
# (weather, move_type) -> multiplier
_WEATHER_DAMAGE_MODS: dict[tuple[str, str], float] = {
    ("rain", "water"): 1.5,
    ("rain", "fire"): 0.5,
    ("sun", "fire"): 1.5,
    ("sun", "water"): 0.5,
}

# Types immune to weather damage
_SANDSTORM_IMMUNE = {"rock", "ground", "steel"}
_HAIL_IMMUNE = {"ice"}

# Moves whose accuracy changes in weather
_WEATHER_ACCURACY: dict[tuple[str, str], int] = {
    ("rain", "Thunder"): 100,
    ("rain", "Hurricane"): 100,
    ("sun", "Thunder"): 50,
    ("hail", "Blizzard"): 100,
}

# Weather-setting moves
WEATHER_MOVES: dict[str, str] = {
    "Rain Dance": "rain",
    "Sunny Day": "sun",
    "Sandstorm": "sandstorm",
    "Hail": "hail",
}

# Held items that extend weather duration (5 -> 8 turns)
_WEATHER_ROCKS: dict[str, str] = {
    "damp_rock": "rain",
    "heat_rock": "sun",
    "smooth_rock": "sandstorm",
    "icy_rock": "hail",
}


def set_weather(
    battle: BattleState,
    weather: str,
    duration: int = 5,
) -> WeatherEvent:
    """Set weather on the battlefield. duration=0 means indefinite (ability)."""
    name = _WEATHER_NAMES.get(weather, weather)
    battle.weather = WeatherState(
        current_weather=weather,
        turns_remaining=duration,
    )
    if duration == 0:
        msg = f"{name} started! (It will last indefinitely)"
    else:
        msg = f"{name} started!"
    return WeatherEvent(
        event_type="weather_set",
        weather=weather,
        message=msg,
    )


def clear_weather(battle: BattleState) -> WeatherEvent | None:
    """Clear the current weather. Returns event or None if already clear."""
    if battle.weather.current_weather is None:
        return None
    old = _WEATHER_NAMES.get(battle.weather.current_weather, battle.weather.current_weather)
    battle.weather = WeatherState()
    return WeatherEvent(
        event_type="weather_ended",
        weather=None,
        message=f"The {old} subsided.",
    )


def decrement_weather_turns(battle: BattleState) -> WeatherEvent | None:
    """Tick down weather duration at end of turn. Returns event if weather ended."""
    w = battle.weather
    if w.current_weather is None:
        return None
    # Indefinite weather (ability-set) never counts down
    if w.turns_remaining == 0:
        return None
    w.turns_remaining -= 1
    if w.turns_remaining <= 0:
        name = _WEATHER_NAMES.get(w.current_weather, w.current_weather)
        w.current_weather = None
        return WeatherEvent(
            event_type="weather_ended",
            weather=None,
            message=f"The {name} subsided.",
        )
    return None


def get_weather_damage_multiplier(move_type: str, weather: str | None) -> float:
    """Return the damage multiplier for a move type under current weather."""
    if weather is None:
        return 1.0
    return _WEATHER_DAMAGE_MODS.get((weather, move_type), 1.0)


def get_weather_accuracy_override(move_name: str, weather: str | None) -> int | None:
    """Return overridden accuracy for a move under current weather, or None."""
    if weather is None:
        return None
    return _WEATHER_ACCURACY.get((weather, move_name))


def is_immune_to_weather_damage(types: list[str], weather: str) -> bool:
    """Check if a Pokemon's types make it immune to end-of-turn weather damage."""
    type_set = set(types)
    if weather == "sandstorm":
        return bool(type_set & _SANDSTORM_IMMUNE)
    if weather == "hail":
        return bool(type_set & _HAIL_IMMUNE)
    return True  # rain/sun don't deal damage


def process_weather_damage(battle: BattleState) -> list[WeatherEvent]:
    """Process end-of-turn weather damage for both Pokemon."""
    weather = battle.weather.current_weather
    if weather not in ("sandstorm", "hail"):
        return []

    events: list[WeatherEvent] = []
    name = _WEATHER_NAMES.get(weather, weather)

    for role, pokemon in [("player", battle.player_pokemon), ("enemy", battle.enemy_pokemon)]:
        if pokemon.current_hp <= 0:
            continue
        if is_immune_to_weather_damage(pokemon.types, weather):
            continue
        dmg = max(1, pokemon.max_hp // 16)
        pokemon.current_hp = max(0, pokemon.current_hp - dmg)
        events.append(WeatherEvent(
            event_type="weather_damage",
            weather=weather,
            pokemon=role,
            damage=dmg,
            message=f"{pokemon.name} is buffeted by the {name}!",
        ))

    return events


def get_sandstorm_spdef_boost(defender: BattlePokemon, weather: str | None) -> float:
    """Return Sp.Def multiplier for Rock types in Sandstorm."""
    if weather != "sandstorm":
        return 1.0
    if "rock" in defender.types:
        return 1.5
    return 1.0


def get_weather_rock_duration(pokemon: BattlePokemon, weather: str) -> int:
    """Return weather duration considering held weather rock items. Default 5, rock extends to 8."""
    if pokemon.held_item:
        rock_weather = _WEATHER_ROCKS.get(pokemon.held_item)
        if rock_weather == weather:
            return 8
    return 5


def process_weather_move(move_name: str, battle: BattleState, user: BattlePokemon | None = None) -> list[WeatherEvent]:
    """Process a weather-setting move. Returns weather events."""
    weather = WEATHER_MOVES.get(move_name)
    if weather is None:
        return []
    duration = get_weather_rock_duration(user, weather) if user else 5
    evt = set_weather(battle, weather, duration=duration)
    return [evt]
