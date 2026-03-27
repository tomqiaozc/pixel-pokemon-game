"""Tests for Sprint 5 QA-B weather bug fixes: type case sensitivity, weather rocks, Sand Veil/Snow Cloak."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.models.battle import BattlePokemon, BattleState, StatStages
from backend.models.pokemon import Move, Stats
from backend.models.weather import WeatherState
from backend.services.ability_service import get_weather_evasion_check
from backend.services.weather_service import get_weather_rock_duration, process_weather_move


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


def _make_battle(**overrides) -> BattleState:
    defaults = dict(
        id="test",
        battle_type="wild",
        player_pokemon=_make_pokemon(name="Player"),
        enemy_pokemon=_make_pokemon(name="Enemy"),
    )
    defaults.update(overrides)
    return BattleState(**defaults)


# ============================================================
# B-04: Type case sensitivity normalization
# ============================================================

class TestTypeCaseNormalization:
    def test_battle_pokemon_types_normalized(self):
        """BattlePokemon types are lowercased on creation."""
        pokemon = _make_pokemon(types=["Fire", "FLYING"])
        assert pokemon.types == ["fire", "flying"]

    def test_move_type_normalized(self):
        """Move type is lowercased on creation."""
        move = Move(name="Ember", type="Fire", power=40, accuracy=100, pp=25)
        assert move.type == "fire"

    def test_mixed_case_types(self):
        """Various case formats all normalize to lowercase."""
        pokemon = _make_pokemon(types=["wAtEr", "Ice"])
        assert pokemon.types == ["water", "ice"]

    def test_already_lowercase_unchanged(self):
        """Lowercase types pass through unchanged."""
        pokemon = _make_pokemon(types=["grass", "poison"])
        assert pokemon.types == ["grass", "poison"]


# ============================================================
# B-01: Held-item weather duration extension
# ============================================================

class TestWeatherRocks:
    def test_damp_rock_extends_rain(self):
        pokemon = _make_pokemon(held_item="damp_rock")
        assert get_weather_rock_duration(pokemon, "rain") == 8

    def test_heat_rock_extends_sun(self):
        pokemon = _make_pokemon(held_item="heat_rock")
        assert get_weather_rock_duration(pokemon, "sun") == 8

    def test_smooth_rock_extends_sandstorm(self):
        pokemon = _make_pokemon(held_item="smooth_rock")
        assert get_weather_rock_duration(pokemon, "sandstorm") == 8

    def test_icy_rock_extends_hail(self):
        pokemon = _make_pokemon(held_item="icy_rock")
        assert get_weather_rock_duration(pokemon, "hail") == 8

    def test_wrong_rock_no_extension(self):
        """Damp Rock doesn't extend sun duration."""
        pokemon = _make_pokemon(held_item="damp_rock")
        assert get_weather_rock_duration(pokemon, "sun") == 5

    def test_no_item_default_duration(self):
        pokemon = _make_pokemon()
        assert get_weather_rock_duration(pokemon, "rain") == 5

    def test_weather_move_uses_rock_duration(self):
        """process_weather_move uses held item to extend duration."""
        user = _make_pokemon(held_item="damp_rock")
        battle = _make_battle()
        events = process_weather_move("Rain Dance", battle, user=user)
        assert len(events) == 1
        assert battle.weather.turns_remaining == 8

    def test_weather_move_default_without_rock(self):
        user = _make_pokemon()
        battle = _make_battle()
        process_weather_move("Rain Dance", battle, user=user)
        assert battle.weather.turns_remaining == 5

    def test_held_item_field_optional(self):
        """BattlePokemon works without held_item."""
        pokemon = _make_pokemon()
        assert pokemon.held_item is None


# ============================================================
# B-02: Sand Veil / Snow Cloak evasion
# ============================================================

class TestSandVeilSnowCloak:
    def test_sand_veil_triggers_in_sandstorm(self):
        pokemon = _make_pokemon(ability_id="sand_veil")
        with patch("backend.services.ability_service.random") as mock_random:
            mock_random.random.return_value = 0.1  # below 0.20 threshold
            assert get_weather_evasion_check(pokemon, "sandstorm") is True

    def test_sand_veil_no_trigger_above_threshold(self):
        pokemon = _make_pokemon(ability_id="sand_veil")
        with patch("backend.services.ability_service.random") as mock_random:
            mock_random.random.return_value = 0.5  # above 0.20
            assert get_weather_evasion_check(pokemon, "sandstorm") is False

    def test_sand_veil_no_trigger_wrong_weather(self):
        pokemon = _make_pokemon(ability_id="sand_veil")
        assert get_weather_evasion_check(pokemon, "rain") is False

    def test_sand_veil_no_trigger_no_weather(self):
        pokemon = _make_pokemon(ability_id="sand_veil")
        assert get_weather_evasion_check(pokemon, None) is False

    def test_snow_cloak_triggers_in_hail(self):
        pokemon = _make_pokemon(ability_id="snow_cloak")
        with patch("backend.services.ability_service.random") as mock_random:
            mock_random.random.return_value = 0.15
            assert get_weather_evasion_check(pokemon, "hail") is True

    def test_snow_cloak_no_trigger_above_threshold(self):
        pokemon = _make_pokemon(ability_id="snow_cloak")
        with patch("backend.services.ability_service.random") as mock_random:
            mock_random.random.return_value = 0.5
            assert get_weather_evasion_check(pokemon, "hail") is False

    def test_snow_cloak_no_trigger_wrong_weather(self):
        pokemon = _make_pokemon(ability_id="snow_cloak")
        assert get_weather_evasion_check(pokemon, "sandstorm") is False

    def test_no_ability_no_evasion(self):
        pokemon = _make_pokemon()
        assert get_weather_evasion_check(pokemon, "sandstorm") is False
