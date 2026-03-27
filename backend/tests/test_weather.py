"""Tests for the Pokemon weather system."""
from __future__ import annotations

from unittest.mock import patch

from backend.models.battle import BattlePokemon, BattleState, StatStages
from backend.models.pokemon import Move, Stats
from backend.models.weather import WeatherEvent, WeatherState
from backend.services.ability_service import (
    get_weather_speed_multiplier,
    process_ability_weather_end_of_turn,
    process_weather_ability_on_switch_in,
)
from backend.services.battle_service import start_battle, process_action
from backend.services.weather_service import (
    WEATHER_MOVES,
    clear_weather,
    decrement_weather_turns,
    get_sandstorm_spdef_boost,
    get_weather_accuracy_override,
    get_weather_damage_multiplier,
    is_immune_to_weather_damage,
    process_weather_damage,
    process_weather_move,
    set_weather,
)
from backend.services.status_service import get_effective_stat


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


def _make_battle(
    player_types=None,
    enemy_types=None,
    player_ability=None,
    enemy_ability=None,
    weather=None,
) -> BattleState:
    player = _make_pokemon(name="Player", types=player_types or ["fire"], ability_id=player_ability)
    enemy = _make_pokemon(name="Enemy", types=enemy_types or ["water"], ability_id=enemy_ability)
    battle = BattleState(
        id="test_weather",
        battle_type="wild",
        player_pokemon=player,
        enemy_pokemon=enemy,
    )
    if weather:
        battle.weather = WeatherState(current_weather=weather, turns_remaining=5)
    return battle


# --- WeatherState model tests ---

class TestWeatherState:
    def test_default_state(self):
        ws = WeatherState()
        assert ws.current_weather is None
        assert ws.turns_remaining == 0

    def test_set_state(self):
        ws = WeatherState(current_weather="rain", turns_remaining=5)
        assert ws.current_weather == "rain"
        assert ws.turns_remaining == 5


# --- set_weather / clear_weather ---

class TestSetClearWeather:
    def test_set_weather_rain(self):
        battle = _make_battle()
        evt = set_weather(battle, "rain", duration=5)
        assert battle.weather.current_weather == "rain"
        assert battle.weather.turns_remaining == 5
        assert evt.event_type == "weather_set"
        assert evt.weather == "rain"

    def test_set_weather_indefinite(self):
        battle = _make_battle()
        evt = set_weather(battle, "sun", duration=0)
        assert battle.weather.turns_remaining == 0
        assert "indefinitely" in evt.message.lower()

    def test_clear_weather(self):
        battle = _make_battle(weather="rain")
        evt = clear_weather(battle)
        assert battle.weather.current_weather is None
        assert evt is not None
        assert evt.event_type == "weather_ended"

    def test_clear_already_clear(self):
        battle = _make_battle()
        evt = clear_weather(battle)
        assert evt is None


# --- decrement_weather_turns ---

class TestDecrementWeather:
    def test_countdown(self):
        battle = _make_battle(weather="rain")
        battle.weather.turns_remaining = 2
        evt = decrement_weather_turns(battle)
        assert evt is None  # not yet expired
        assert battle.weather.turns_remaining == 1

    def test_expires(self):
        battle = _make_battle(weather="rain")
        battle.weather.turns_remaining = 1
        evt = decrement_weather_turns(battle)
        assert evt is not None
        assert evt.event_type == "weather_ended"
        assert battle.weather.current_weather is None

    def test_indefinite_never_expires(self):
        battle = _make_battle(weather="sun")
        battle.weather.turns_remaining = 0  # indefinite
        evt = decrement_weather_turns(battle)
        assert evt is None
        assert battle.weather.current_weather == "sun"

    def test_no_weather(self):
        battle = _make_battle()
        evt = decrement_weather_turns(battle)
        assert evt is None


# --- Damage multipliers ---

class TestWeatherDamageMultiplier:
    def test_rain_boosts_water(self):
        assert get_weather_damage_multiplier("water", "rain") == 1.5

    def test_rain_weakens_fire(self):
        assert get_weather_damage_multiplier("fire", "rain") == 0.5

    def test_sun_boosts_fire(self):
        assert get_weather_damage_multiplier("fire", "sun") == 1.5

    def test_sun_weakens_water(self):
        assert get_weather_damage_multiplier("water", "sun") == 0.5

    def test_no_weather_neutral(self):
        assert get_weather_damage_multiplier("fire", None) == 1.0

    def test_unaffected_type(self):
        assert get_weather_damage_multiplier("grass", "rain") == 1.0


# --- Accuracy overrides ---

class TestWeatherAccuracy:
    def test_thunder_in_rain(self):
        assert get_weather_accuracy_override("Thunder", "rain") == 100

    def test_thunder_in_sun(self):
        assert get_weather_accuracy_override("Thunder", "sun") == 50

    def test_blizzard_in_hail(self):
        assert get_weather_accuracy_override("Blizzard", "hail") == 100

    def test_normal_move_no_override(self):
        assert get_weather_accuracy_override("Tackle", "rain") is None

    def test_no_weather(self):
        assert get_weather_accuracy_override("Thunder", None) is None


# --- Weather damage immunities ---

class TestWeatherImmunity:
    def test_rock_immune_sandstorm(self):
        assert is_immune_to_weather_damage(["rock"], "sandstorm") is True

    def test_ground_immune_sandstorm(self):
        assert is_immune_to_weather_damage(["ground"], "sandstorm") is True

    def test_steel_immune_sandstorm(self):
        assert is_immune_to_weather_damage(["steel"], "sandstorm") is True

    def test_fire_not_immune_sandstorm(self):
        assert is_immune_to_weather_damage(["fire"], "sandstorm") is False

    def test_ice_immune_hail(self):
        assert is_immune_to_weather_damage(["ice"], "hail") is True

    def test_water_not_immune_hail(self):
        assert is_immune_to_weather_damage(["water"], "hail") is False

    def test_rain_no_damage(self):
        assert is_immune_to_weather_damage(["fire"], "rain") is True

    def test_sun_no_damage(self):
        assert is_immune_to_weather_damage(["fire"], "sun") is True


# --- process_weather_damage ---

class TestProcessWeatherDamage:
    def test_sandstorm_damages_non_immune(self):
        battle = _make_battle(player_types=["fire"], enemy_types=["water"], weather="sandstorm")
        events = process_weather_damage(battle)
        assert len(events) == 2  # both take damage
        for evt in events:
            assert evt.event_type == "weather_damage"
            assert evt.damage > 0

    def test_sandstorm_skips_immune(self):
        battle = _make_battle(player_types=["rock"], enemy_types=["water"], weather="sandstorm")
        events = process_weather_damage(battle)
        assert len(events) == 1  # only enemy takes damage
        assert events[0].pokemon == "enemy"

    def test_hail_damages_non_ice(self):
        battle = _make_battle(player_types=["fire"], enemy_types=["ice"], weather="hail")
        events = process_weather_damage(battle)
        assert len(events) == 1
        assert events[0].pokemon == "player"

    def test_rain_no_damage(self):
        battle = _make_battle(weather="rain")
        events = process_weather_damage(battle)
        assert len(events) == 0

    def test_sun_no_damage(self):
        battle = _make_battle(weather="sun")
        events = process_weather_damage(battle)
        assert len(events) == 0

    def test_damage_is_1_16th(self):
        battle = _make_battle(player_types=["fire"], weather="sandstorm")
        expected_dmg = max(1, battle.player_pokemon.max_hp // 16)
        hp_before = battle.player_pokemon.current_hp
        process_weather_damage(battle)
        assert battle.player_pokemon.current_hp == hp_before - expected_dmg

    def test_fainted_pokemon_skipped(self):
        battle = _make_battle(player_types=["fire"], weather="sandstorm")
        battle.player_pokemon.current_hp = 0
        events = process_weather_damage(battle)
        player_events = [e for e in events if e.pokemon == "player"]
        assert len(player_events) == 0


# --- Sandstorm Sp.Def boost ---

class TestSandstormSpDefBoost:
    def test_rock_type_boosted(self):
        p = _make_pokemon(types=["rock"])
        assert get_sandstorm_spdef_boost(p, "sandstorm") == 1.5

    def test_non_rock_not_boosted(self):
        p = _make_pokemon(types=["fire"])
        assert get_sandstorm_spdef_boost(p, "sandstorm") == 1.0

    def test_no_weather(self):
        p = _make_pokemon(types=["rock"])
        assert get_sandstorm_spdef_boost(p, None) == 1.0


# --- Weather moves ---

class TestWeatherMoves:
    def test_rain_dance(self):
        battle = _make_battle()
        events = process_weather_move("Rain Dance", battle)
        assert len(events) == 1
        assert battle.weather.current_weather == "rain"

    def test_sunny_day(self):
        battle = _make_battle()
        events = process_weather_move("Sunny Day", battle)
        assert battle.weather.current_weather == "sun"

    def test_sandstorm_move(self):
        battle = _make_battle()
        events = process_weather_move("Sandstorm", battle)
        assert battle.weather.current_weather == "sandstorm"

    def test_hail_move(self):
        battle = _make_battle()
        events = process_weather_move("Hail", battle)
        assert battle.weather.current_weather == "hail"

    def test_non_weather_move(self):
        battle = _make_battle()
        events = process_weather_move("Tackle", battle)
        assert len(events) == 0
        assert battle.weather.current_weather is None

    def test_weather_move_5_turn_duration(self):
        battle = _make_battle()
        process_weather_move("Rain Dance", battle)
        assert battle.weather.turns_remaining == 5


# --- Weather speed abilities ---

class TestWeatherSpeedAbilities:
    def test_swift_swim_in_rain(self):
        p = _make_pokemon(ability_id="swift_swim")
        assert get_weather_speed_multiplier(p, "rain") == 2.0

    def test_swift_swim_no_rain(self):
        p = _make_pokemon(ability_id="swift_swim")
        assert get_weather_speed_multiplier(p, "sun") == 1.0

    def test_chlorophyll_in_sun(self):
        p = _make_pokemon(ability_id="chlorophyll")
        assert get_weather_speed_multiplier(p, "sun") == 2.0

    def test_sand_rush_in_sandstorm(self):
        p = _make_pokemon(ability_id="sand_rush")
        assert get_weather_speed_multiplier(p, "sandstorm") == 2.0

    def test_no_ability(self):
        p = _make_pokemon()
        assert get_weather_speed_multiplier(p, "rain") == 1.0

    def test_no_weather(self):
        p = _make_pokemon(ability_id="swift_swim")
        assert get_weather_speed_multiplier(p, None) == 1.0


# --- get_effective_stat with weather ---

class TestEffectiveStatWeather:
    def test_speed_doubled_swift_swim_rain(self):
        p = _make_pokemon(ability_id="swift_swim")
        base_speed = get_effective_stat(p, "speed")
        weather_speed = get_effective_stat(p, "speed", "rain")
        assert weather_speed == base_speed * 2

    def test_speed_not_doubled_wrong_weather(self):
        p = _make_pokemon(ability_id="swift_swim")
        base_speed = get_effective_stat(p, "speed")
        weather_speed = get_effective_stat(p, "speed", "sun")
        assert weather_speed == base_speed

    def test_attack_not_affected_by_weather(self):
        p = _make_pokemon(ability_id="swift_swim")
        base_attack = get_effective_stat(p, "attack")
        weather_attack = get_effective_stat(p, "attack", "rain")
        assert weather_attack == base_attack


# --- Weather-setting abilities ---

class TestWeatherSettingAbilities:
    def test_drizzle(self):
        battle = _make_battle()
        p = _make_pokemon(ability_id="drizzle")
        events = process_weather_ability_on_switch_in(p, "player", battle)
        assert len(events) == 1
        assert battle.weather.current_weather == "rain"
        assert battle.weather.turns_remaining == 0  # indefinite

    def test_drought(self):
        battle = _make_battle()
        p = _make_pokemon(ability_id="drought")
        events = process_weather_ability_on_switch_in(p, "player", battle)
        assert battle.weather.current_weather == "sun"

    def test_sand_stream(self):
        battle = _make_battle()
        p = _make_pokemon(ability_id="sand_stream")
        events = process_weather_ability_on_switch_in(p, "player", battle)
        assert battle.weather.current_weather == "sandstorm"

    def test_snow_warning(self):
        battle = _make_battle()
        p = _make_pokemon(ability_id="snow_warning")
        events = process_weather_ability_on_switch_in(p, "player", battle)
        assert battle.weather.current_weather == "hail"

    def test_non_weather_ability(self):
        battle = _make_battle()
        p = _make_pokemon(ability_id="blaze")
        events = process_weather_ability_on_switch_in(p, "player", battle)
        assert len(events) == 0
        assert battle.weather.current_weather is None


# --- Rain Dish ability ---

class TestRainDish:
    def test_heals_in_rain(self):
        p = _make_pokemon(ability_id="rain_dish", hp=100)
        p.current_hp = 80
        events = process_ability_weather_end_of_turn(p, "player", "rain")
        assert len(events) == 1
        assert p.current_hp > 80

    def test_no_heal_no_rain(self):
        p = _make_pokemon(ability_id="rain_dish", hp=100)
        p.current_hp = 80
        events = process_ability_weather_end_of_turn(p, "player", "sun")
        assert len(events) == 0
        assert p.current_hp == 80

    def test_no_overheal(self):
        p = _make_pokemon(ability_id="rain_dish", hp=100)
        p.current_hp = 100  # already full
        events = process_ability_weather_end_of_turn(p, "player", "rain")
        assert len(events) == 0
        assert p.current_hp == 100

    def test_fainted_no_heal(self):
        p = _make_pokemon(ability_id="rain_dish", hp=100)
        p.current_hp = 0
        events = process_ability_weather_end_of_turn(p, "player", "rain")
        assert len(events) == 0


# --- Weather moves data ---

class TestWeatherMovesData:
    def test_weather_moves_dict(self):
        assert WEATHER_MOVES["Rain Dance"] == "rain"
        assert WEATHER_MOVES["Sunny Day"] == "sun"
        assert WEATHER_MOVES["Sandstorm"] == "sandstorm"
        assert WEATHER_MOVES["Hail"] == "hail"


# --- Integration: battle with weather ---

class TestBattleWeatherIntegration:
    def test_battle_state_has_weather(self):
        battle = start_battle(
            _make_pokemon(name="Player").model_dump(),
            _make_pokemon(name="Enemy").model_dump(),
        )
        assert battle.weather.current_weather is None
        assert battle.weather.turns_remaining == 0

    def test_weather_move_in_battle(self):
        """Test that using a weather move in battle sets weather."""
        player = _make_pokemon(name="Player", types=["water"])
        player.moves = [Move(name="Rain Dance", type="water", power=0, accuracy=100, pp=5)]
        enemy = _make_pokemon(name="Enemy", types=["fire"])
        enemy.moves = [Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35, contact=True)]

        battle = start_battle(player.model_dump(), enemy.model_dump())

        with patch("backend.services.battle_service.random.randint", return_value=1), \
             patch("backend.services.battle_service.random.uniform", return_value=1.0):
            result = process_action(battle.id, "fight", 0)

        assert result is not None
        assert battle.weather.current_weather == "rain"
        assert len(result.weather_events) > 0
