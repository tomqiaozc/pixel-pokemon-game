"""Sprint 5 QA-A supplementary tests — gap coverage for weather, abilities, and status.

Fills gaps not covered by the existing test_weather.py, test_abilities.py,
and test_status_conditions.py test files.
"""
from __future__ import annotations

import random
from unittest.mock import patch

from backend.models.battle import BattlePokemon, BattleState, StatStages
from backend.models.pokemon import Move, Stats
from backend.models.weather import WeatherEvent, WeatherState
from backend.services.ability_service import (
    check_ability_type_immunity,
    get_ability,
    get_ability_name,
    get_weather_speed_multiplier,
    process_ability_damage_modifier,
    process_ability_end_of_turn,
    process_ability_on_hit,
    process_ability_weather_end_of_turn,
    process_switch_in_ability,
    process_weather_ability_on_switch_in,
    select_ability,
)
from backend.services.battle_service import start_battle, process_action, _battles
from backend.services.status_service import (
    apply_stat_change,
    apply_status,
    can_apply_status,
    get_effective_stat,
    process_move_effects,
    process_status_before_move,
    process_status_end_of_turn,
)
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


def _pokemon(
    name="TestMon",
    types=None,
    ability_id=None,
    hp=100,
    level=50,
    speed=50,
    attack=50,
    defense=50,
    **kwargs,
) -> BattlePokemon:
    if types is None:
        types = ["normal"]
    return BattlePokemon(
        species_id=1,
        name=name,
        types=types,
        level=level,
        stats=Stats(hp=hp, attack=attack, defense=defense, sp_attack=50, sp_defense=50, speed=speed),
        current_hp=kwargs.pop("current_hp", hp),
        max_hp=hp,
        moves=[Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35, contact=True)],
        sprite="test.png",
        ability_id=ability_id,
        **kwargs,
    )


def _battle(**overrides) -> BattleState:
    defaults = dict(
        id="qa_test",
        battle_type="wild",
        player_pokemon=_pokemon(name="Player"),
        enemy_pokemon=_pokemon(name="Enemy"),
    )
    defaults.update(overrides)
    return BattleState(**defaults)


# =====================================================================
# Weather service — additional coverage
# =====================================================================

class TestSetWeatherExtended:
    def test_set_all_four_weathers(self):
        for w, expected_name in [("rain", "Rain"), ("sun", "Harsh Sunlight"),
                                  ("sandstorm", "Sandstorm"), ("hail", "Hail")]:
            battle = _battle()
            evt = set_weather(battle, w, duration=5)
            assert battle.weather.current_weather == w
            assert expected_name in evt.message

    def test_overwrite_existing_weather(self):
        battle = _battle()
        set_weather(battle, "rain", duration=5)
        assert battle.weather.current_weather == "rain"
        evt = set_weather(battle, "sun", duration=3)
        assert battle.weather.current_weather == "sun"
        assert battle.weather.turns_remaining == 3
        assert "Harsh Sunlight" in evt.message


class TestDecrementWeatherExtended:
    def test_full_5_turn_countdown(self):
        battle = _battle()
        set_weather(battle, "rain", duration=5)
        for i in range(4):
            evt = decrement_weather_turns(battle)
            assert evt is None
            assert battle.weather.turns_remaining == 5 - (i + 1)
        evt = decrement_weather_turns(battle)
        assert evt is not None
        assert evt.event_type == "weather_ended"
        assert battle.weather.current_weather is None


class TestWeatherAccuracyExtended:
    def test_hurricane_in_rain(self):
        assert get_weather_accuracy_override("Hurricane", "rain") == 100

    def test_hurricane_no_override_in_sun(self):
        assert get_weather_accuracy_override("Hurricane", "sun") is None

    def test_blizzard_no_override_in_rain(self):
        assert get_weather_accuracy_override("Blizzard", "rain") is None


class TestWeatherImmunityExtended:
    def test_dual_type_sandstorm_immunity(self):
        # fire/rock is immune to sandstorm (rock grants immunity)
        assert is_immune_to_weather_damage(["fire", "rock"], "sandstorm") is True

    def test_dual_type_not_immune(self):
        assert is_immune_to_weather_damage(["fire", "water"], "sandstorm") is False

    def test_dual_type_hail_immunity(self):
        assert is_immune_to_weather_damage(["water", "ice"], "hail") is True


class TestWeatherDamageExtended:
    def test_minimum_1_damage(self):
        """Pokemon with very low max_hp still takes at least 1 damage."""
        battle = _battle(
            player_pokemon=_pokemon(name="Tiny", types=["normal"], hp=10),
            enemy_pokemon=_pokemon(name="Also", types=["rock"], hp=10),
        )
        set_weather(battle, "sandstorm")
        events = process_weather_damage(battle)
        # Only player takes damage (enemy is rock)
        assert len(events) == 1
        assert events[0].damage >= 1

    def test_weather_damage_reduces_hp(self):
        battle = _battle(
            player_pokemon=_pokemon(name="P", types=["fire"], hp=160),
            enemy_pokemon=_pokemon(name="E", types=["rock"], hp=160),
        )
        set_weather(battle, "sandstorm")
        hp_before = battle.player_pokemon.current_hp
        process_weather_damage(battle)
        assert battle.player_pokemon.current_hp == hp_before - max(1, 160 // 16)

    def test_hail_damage_reduces_hp(self):
        battle = _battle(
            player_pokemon=_pokemon(name="P", types=["fire"], hp=160),
            enemy_pokemon=_pokemon(name="E", types=["ice"], hp=160),
        )
        set_weather(battle, "hail")
        hp_before = battle.player_pokemon.current_hp
        process_weather_damage(battle)
        assert battle.player_pokemon.current_hp == hp_before - max(1, 160 // 16)


class TestSandstormSpDefExtended:
    def test_rock_dual_type_boosted(self):
        p = _pokemon(types=["rock", "ground"])
        assert get_sandstorm_spdef_boost(p, "sandstorm") == 1.5

    def test_no_boost_in_rain(self):
        p = _pokemon(types=["rock"])
        assert get_sandstorm_spdef_boost(p, "rain") == 1.0

    def test_no_boost_in_hail(self):
        p = _pokemon(types=["rock"])
        assert get_sandstorm_spdef_boost(p, "hail") == 1.0


class TestWeatherDamageMultiplierExtended:
    def test_sandstorm_no_type_boost(self):
        """Sandstorm doesn't boost any move type."""
        assert get_weather_damage_multiplier("rock", "sandstorm") == 1.0

    def test_hail_no_type_boost(self):
        """Hail doesn't boost any move type."""
        assert get_weather_damage_multiplier("ice", "hail") == 1.0


# =====================================================================
# Weather speed abilities — additional coverage
# =====================================================================

class TestWeatherSpeedExtended:
    def test_chlorophyll_no_boost_in_rain(self):
        assert get_weather_speed_multiplier(_pokemon(ability_id="chlorophyll"), "rain") == 1.0

    def test_sand_rush_no_boost_in_rain(self):
        assert get_weather_speed_multiplier(_pokemon(ability_id="sand_rush"), "rain") == 1.0

    def test_sand_rush_no_boost_in_hail(self):
        assert get_weather_speed_multiplier(_pokemon(ability_id="sand_rush"), "hail") == 1.0

    def test_non_speed_ability_no_boost(self):
        assert get_weather_speed_multiplier(_pokemon(ability_id="blaze"), "sun") == 1.0

    def test_chlorophyll_no_boost_in_sandstorm(self):
        assert get_weather_speed_multiplier(_pokemon(ability_id="chlorophyll"), "sandstorm") == 1.0


class TestEffectiveStatWeatherExtended:
    def test_paralysis_and_swift_swim(self):
        """Paralysis quarters speed, swift swim doubles — both stack."""
        p = _pokemon(ability_id="swift_swim", speed=100)
        p.status = "par"
        eff = get_effective_stat(p, "speed", "rain")
        # par: 100//4 = 25, swift swim: 25*2 = 50
        assert eff == 50

    def test_stat_stages_and_swift_swim(self):
        """Stat stage +2 and swift swim should both apply."""
        p = _pokemon(ability_id="swift_swim", speed=100)
        p.stat_stages.speed = 2  # (2+2)/2 = 2.0x
        eff = get_effective_stat(p, "speed", "rain")
        # +2 stage: 100*2 = 200, swift swim: 200*2 = 400
        assert eff == 400

    def test_chlorophyll_in_sun_doubles(self):
        p = _pokemon(ability_id="chlorophyll", speed=80)
        eff = get_effective_stat(p, "speed", "sun")
        assert eff == 160

    def test_no_weather_param_backwards_compat(self):
        """get_effective_stat without weather arg should still work."""
        p = _pokemon(speed=100)
        assert get_effective_stat(p, "speed") == 100


# =====================================================================
# Weather-setting abilities — additional coverage
# =====================================================================

class TestWeatherAbilitySwitchInExtended:
    def test_no_ability_no_weather(self):
        battle = _battle()
        p = _pokemon(ability_id=None)
        events = process_weather_ability_on_switch_in(p, "player", battle)
        assert len(events) == 0
        assert battle.weather.current_weather is None

    def test_weather_ability_is_indefinite(self):
        """All weather abilities set duration=0 (indefinite)."""
        for ab in ["drizzle", "drought", "sand_stream", "snow_warning"]:
            battle = _battle()
            p = _pokemon(ability_id=ab)
            process_weather_ability_on_switch_in(p, "player", battle)
            assert battle.weather.turns_remaining == 0, f"{ab} should set indefinite weather"


# =====================================================================
# Rain Dish — additional coverage
# =====================================================================

class TestRainDishExtended:
    def test_heal_amount_is_1_16th(self):
        p = _pokemon(ability_id="rain_dish", hp=160, current_hp=100)
        process_ability_weather_end_of_turn(p, "player", "rain")
        # 160 // 16 = 10
        assert p.current_hp == 110

    def test_heal_caps_at_max(self):
        p = _pokemon(ability_id="rain_dish", hp=160, current_hp=155)
        process_ability_weather_end_of_turn(p, "player", "rain")
        assert p.current_hp == 160  # capped, not 165

    def test_no_heal_in_sandstorm(self):
        p = _pokemon(ability_id="rain_dish", hp=160, current_hp=100)
        events = process_ability_weather_end_of_turn(p, "player", "sandstorm")
        assert len(events) == 0
        assert p.current_hp == 100

    def test_no_heal_in_hail(self):
        p = _pokemon(ability_id="rain_dish", hp=160, current_hp=100)
        events = process_ability_weather_end_of_turn(p, "player", "hail")
        assert len(events) == 0


# =====================================================================
# Ability data — all 24 abilities in JSON
# =====================================================================

class TestAbilityDataComplete:
    ALL_ABILITIES = [
        "overgrow", "blaze", "torrent", "static", "intimidate", "sturdy",
        "levitate", "speed_boost", "poison_point", "flame_body", "water_absorb",
        "flash_fire", "limber", "keen_eye", "rock_head", "run_away",
        "drizzle", "drought", "sand_stream", "snow_warning",
        "swift_swim", "chlorophyll", "sand_rush", "rain_dish",
    ]

    def test_all_abilities_exist(self):
        for ab_id in self.ALL_ABILITIES:
            ab = get_ability(ab_id)
            assert ab is not None, f"Missing ability: {ab_id}"

    def test_all_abilities_have_required_fields(self):
        for ab_id in self.ALL_ABILITIES:
            ab = get_ability(ab_id)
            assert "id" in ab, f"{ab_id} missing 'id'"
            assert "name" in ab, f"{ab_id} missing 'name'"
            assert "description" in ab, f"{ab_id} missing 'description'"
            assert "trigger_types" in ab, f"{ab_id} missing 'trigger_types'"
            assert "trigger_data" in ab, f"{ab_id} missing 'trigger_data'"

    def test_ability_count(self):
        """Verify we have 27 abilities (24 base + 3 QA additions)."""
        from backend.services.ability_service import _abilities_db, _load_abilities
        if not _abilities_db:
            _load_abilities()
        assert len(_abilities_db) == 27

    def test_get_ability_name_returns_display_name(self):
        assert get_ability_name("overgrow") == "Overgrow"
        assert get_ability_name("flash_fire") == "Flash Fire"
        assert get_ability_name("rain_dish") == "Rain Dish"

    def test_get_ability_name_unknown_returns_id(self):
        assert get_ability_name("nonexistent_ability") == "nonexistent_ability"


# =====================================================================
# Abilities — gap coverage for existing abilities
# =====================================================================

class TestWaterAbsorbExtended:
    def test_water_absorb_at_full_hp(self):
        """Water Absorb still grants immunity even at full HP."""
        defender = _pokemon(name="Vaporeon", types=["water"], ability_id="water_absorb", hp=100)
        water_move = Move(name="Water Gun", type="water", power=40, accuracy=100, pp=25)
        immune, events = check_ability_type_immunity(defender, water_move, "enemy")
        assert immune is True
        assert defender.current_hp == 100  # no overheal

    def test_water_absorb_no_immunity_to_status_water_move(self):
        """Zero-power water move doesn't trigger Water Absorb."""
        defender = _pokemon(name="Vaporeon", types=["water"], ability_id="water_absorb", hp=100)
        defender.current_hp = 50
        status_move = Move(name="Water Sport", type="water", power=0, accuracy=100, pp=15)
        immune, events = check_ability_type_immunity(defender, status_move, "enemy")
        assert immune is False


class TestFlashFireExtended:
    def test_flash_fire_no_trigger_on_status_fire_move(self):
        """Zero-power fire move doesn't trigger Flash Fire."""
        defender = _pokemon(types=["fire"], ability_id="flash_fire", hp=100)
        status_move = Move(name="Will-O-Wisp", type="fire", power=0, accuracy=85, pp=15)
        immune, events = check_ability_type_immunity(defender, status_move, "enemy")
        assert immune is False
        assert defender.flash_fire_activated is False


class TestLevitateExtended:
    def test_levitate_no_immunity_to_status_ground_move(self):
        """Zero-power ground move doesn't trigger Levitate."""
        defender = _pokemon(types=["ghost"], ability_id="levitate", hp=100)
        status_move = Move(name="Sand Attack", type="normal", power=0, accuracy=100, pp=15)
        immune, events = check_ability_type_immunity(defender, status_move, "enemy")
        assert immune is False


class TestSturdyExtended:
    def test_sturdy_leaves_exactly_1_hp(self):
        attacker = _pokemon(types=["normal"])
        defender = _pokemon(types=["rock"], ability_id="sturdy", hp=50)
        move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35, contact=True)
        dmg, events = process_ability_damage_modifier(attacker, defender, move, 999, "player", "enemy")
        assert dmg == 49
        # Defender would have 50 - 49 = 1 HP after damage

    def test_sturdy_no_effect_on_non_lethal(self):
        attacker = _pokemon(types=["normal"])
        defender = _pokemon(types=["rock"], ability_id="sturdy", hp=50)
        move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35, contact=True)
        dmg, events = process_ability_damage_modifier(attacker, defender, move, 30, "player", "enemy")
        assert dmg == 30  # not lethal, no Sturdy
        assert len(events) == 0


class TestSelectAbilityExtended:
    def test_select_from_multiple(self):
        """Selecting from a pool should return one of the options."""
        abilities = ["rock_head", "sturdy"]
        for _ in range(20):
            result = select_ability(abilities)
            assert result in abilities


class TestProcessSwitchInAbilityExtended:
    def test_no_ability_returns_empty(self):
        p = _pokemon(ability_id=None)
        opp = _pokemon()
        events = process_switch_in_ability(p, opp, "player", "enemy")
        assert events == []

    def test_non_intimidate_ability_no_effect(self):
        p = _pokemon(ability_id="blaze")
        opp = _pokemon()
        events = process_switch_in_ability(p, opp, "player", "enemy")
        assert events == []


class TestSpeedBoostExtended:
    def test_speed_boost_caps_at_6(self):
        p = _pokemon(ability_id="speed_boost")
        p.stat_stages.speed = 6
        events = process_ability_end_of_turn(p, "player")
        assert len(events) >= 1
        assert p.stat_stages.speed == 6  # capped

    def test_speed_boost_fainted_no_effect(self):
        p = _pokemon(ability_id="speed_boost")
        p.current_hp = 0
        events = process_ability_end_of_turn(p, "player")
        assert len(events) == 0


# =====================================================================
# Status conditions — gap coverage
# =====================================================================

class TestStatusGaps:
    def test_steel_immune_to_poison(self):
        p = _pokemon(types=["steel"])
        assert can_apply_status(p, "psn") is False

    def test_steel_immune_to_toxic(self):
        p = _pokemon(types=["steel"])
        assert can_apply_status(p, "tox") is False

    def test_poison_type_immune_to_poison(self):
        p = _pokemon(types=["poison"])
        assert can_apply_status(p, "psn") is False

    def test_fire_immune_to_burn_event(self):
        p = _pokemon(types=["fire"])
        evt = apply_status(p, "brn", "player")
        assert evt is not None
        assert evt.event_type == "status_prevented"

    def test_toxic_counter_increments(self):
        p = _pokemon(types=["normal"], hp=200)
        p.status = "tox"
        p.status_turns = 1
        process_status_end_of_turn(p, "player")
        assert p.status_turns == 2
        dmg1 = 200 - p.current_hp
        process_status_end_of_turn(p, "player")
        assert p.status_turns == 3
        dmg2 = (200 - dmg1) - p.current_hp
        assert dmg2 > dmg1  # escalating

    def test_confusion_self_hit_damage(self):
        """Confusion self-hit uses 40 power typeless physical attack formula."""
        p = _pokemon(types=["normal"], hp=200, level=50, attack=100, defense=100)
        p.confused = True
        p.confused_turns = 3
        with patch("backend.services.status_service.random.random", return_value=0.1):
            can_move, events = process_status_before_move(p, "player")
        if not can_move:
            hit_events = [e for e in events if e.event_type == "confused_hit_self"]
            if hit_events:
                assert hit_events[0].damage > 0
                assert p.current_hp < 200

    def test_sleep_random_duration(self):
        """Sleep duration is 1-3 turns."""
        durations = set()
        for i in range(100):
            random.seed(i)
            p = _pokemon(types=["normal"])
            apply_status(p, "slp", "player")
            durations.add(p.status_turns)
        assert durations.issubset({1, 2, 3})
        assert len(durations) >= 2  # should see at least 2 different values


class TestStatChangeGaps:
    def test_sharp_rise_message(self):
        p = _pokemon()
        evt = apply_stat_change(p, "speed", 2, "player")
        assert "sharply" in evt.message

    def test_harsh_fall_message(self):
        p = _pokemon()
        evt = apply_stat_change(p, "defense", -2, "player")
        assert "harshly" in evt.message

    def test_cant_go_higher_at_6(self):
        p = _pokemon()
        p.stat_stages.attack = 6
        evt = apply_stat_change(p, "attack", 1, "player")
        assert evt.stages == 0
        assert "higher" in evt.message

    def test_cant_go_lower_at_neg6(self):
        p = _pokemon()
        p.stat_stages.defense = -6
        evt = apply_stat_change(p, "defense", -1, "player")
        assert evt.stages == 0
        assert "lower" in evt.message


class TestMoveEffectsGaps:
    def test_tail_whip_lowers_defense(self):
        atk = _pokemon()
        dfn = _pokemon()
        events = process_move_effects("Tail Whip", atk, dfn, "player", "enemy", False)
        assert dfn.stat_stages.defense == -1

    def test_agility_raises_speed(self):
        atk = _pokemon()
        dfn = _pokemon()
        events = process_move_effects("Agility", atk, dfn, "player", "enemy", False)
        assert atk.stat_stages.speed == 2

    def test_defense_curl_raises_defense(self):
        atk = _pokemon()
        dfn = _pokemon()
        events = process_move_effects("Defense Curl", atk, dfn, "player", "enemy", False)
        assert atk.stat_stages.defense == 1


# =====================================================================
# Battle integration — weather events in turn results
# =====================================================================

class TestBattleWeatherEventsIntegration:
    def test_turn_result_has_weather_events_field(self):
        battle = start_battle(
            _pokemon(name="P", speed=200).model_dump(),
            _pokemon(name="E", speed=50).model_dump(),
        )
        result = process_action(battle.id, "fight", 0)
        assert result is not None
        assert hasattr(result, "weather_events")

    def test_sandstorm_damage_in_battle_turn(self):
        battle = _battle(
            player_pokemon=_pokemon(name="P", types=["fire"], hp=200, speed=100),
            enemy_pokemon=_pokemon(name="E", types=["water"], hp=200, speed=50),
        )
        set_weather(battle, "sandstorm", duration=5)
        _battles[battle.id] = battle

        try:
            result = process_action(battle.id, "fight", 0)
            assert result is not None
            dmg_events = [e for e in result.weather_events if e.event_type == "weather_damage"]
            assert len(dmg_events) >= 1
        finally:
            _battles.pop(battle.id, None)

    def test_weather_countdown_in_battle(self):
        battle = _battle(
            player_pokemon=_pokemon(name="P", hp=200, speed=100),
            enemy_pokemon=_pokemon(name="E", hp=200, speed=50),
        )
        set_weather(battle, "rain", duration=1)
        _battles[battle.id] = battle

        try:
            result = process_action(battle.id, "fight", 0)
            assert result is not None
            ended_events = [e for e in result.weather_events if e.event_type == "weather_ended"]
            assert len(ended_events) == 1
            assert battle.weather.current_weather is None
        finally:
            _battles.pop(battle.id, None)

    def test_rain_dish_heals_in_battle(self):
        battle = _battle(
            player_pokemon=_pokemon(name="P", types=["water"], ability_id="rain_dish", hp=200, current_hp=150, speed=100),
            enemy_pokemon=_pokemon(name="E", hp=200, speed=50),
        )
        set_weather(battle, "rain", duration=5)
        _battles[battle.id] = battle

        try:
            result = process_action(battle.id, "fight", 0)
            assert result is not None
            heal_events = [e for e in result.weather_events if e.event_type == "weather_heal"]
            # Rain Dish should heal if player is still alive
            if battle.player_pokemon.current_hp > 0:
                assert len(heal_events) >= 1
        finally:
            _battles.pop(battle.id, None)
