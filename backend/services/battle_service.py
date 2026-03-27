from __future__ import annotations

import math
import random
import uuid

from ..models.battle import (
    BattlePokemon,
    BattleState,
    StatusEvent,
    TurnEvent,
    TurnResult,
)
from ..models.pokemon import Move
from .encounter_service import get_move_data
from .status_service import (
    get_effective_stat,
    process_move_effects,
    process_status_before_move,
    process_status_end_of_turn,
)
from .ability_service import (
    check_ability_type_immunity,
    process_ability_damage_modifier,
    process_ability_end_of_turn,
    process_ability_on_hit,
    process_switch_in_ability,
)

# In-memory battle storage
_battles: dict[str, BattleState] = {}

# Type effectiveness chart
# Keys: (attacking_type, defending_type) -> multiplier
_TYPE_CHART: dict[tuple[str, str], float] = {
    # Fire
    ("fire", "grass"): 2.0,
    ("fire", "water"): 0.5,
    ("fire", "fire"): 0.5,
    ("fire", "rock"): 0.5,
    ("fire", "bug"): 2.0,
    ("fire", "ice"): 2.0,
    ("fire", "steel"): 2.0,
    ("fire", "dragon"): 0.5,
    # Water
    ("water", "fire"): 2.0,
    ("water", "water"): 0.5,
    ("water", "grass"): 0.5,
    ("water", "ground"): 2.0,
    ("water", "rock"): 2.0,
    ("water", "dragon"): 0.5,
    # Grass
    ("grass", "fire"): 0.5,
    ("grass", "water"): 2.0,
    ("grass", "grass"): 0.5,
    ("grass", "poison"): 0.5,
    ("grass", "ground"): 2.0,
    ("grass", "flying"): 0.5,
    ("grass", "bug"): 0.5,
    ("grass", "rock"): 2.0,
    ("grass", "dragon"): 0.5,
    ("grass", "steel"): 0.5,
    # Electric
    ("electric", "water"): 2.0,
    ("electric", "electric"): 0.5,
    ("electric", "grass"): 0.5,
    ("electric", "ground"): 0.0,
    ("electric", "flying"): 2.0,
    ("electric", "dragon"): 0.5,
    # Normal
    ("normal", "rock"): 0.5,
    ("normal", "ghost"): 0.0,
    ("normal", "steel"): 0.5,
    # Flying
    ("flying", "electric"): 0.5,
    ("flying", "rock"): 0.5,
    ("flying", "grass"): 2.0,
    ("flying", "fighting"): 2.0,
    ("flying", "bug"): 2.0,
    ("flying", "steel"): 0.5,
    # Poison
    ("poison", "poison"): 0.5,
    ("poison", "ground"): 0.5,
    ("poison", "rock"): 0.5,
    ("poison", "ghost"): 0.5,
    ("poison", "grass"): 2.0,
    ("poison", "steel"): 0.0,
    ("poison", "fairy"): 2.0,
    # Ground
    ("ground", "fire"): 2.0,
    ("ground", "electric"): 2.0,
    ("ground", "grass"): 0.5,
    ("ground", "poison"): 2.0,
    ("ground", "flying"): 0.0,
    ("ground", "bug"): 0.5,
    ("ground", "rock"): 2.0,
    ("ground", "steel"): 2.0,
    # Psychic
    ("psychic", "fighting"): 2.0,
    ("psychic", "poison"): 2.0,
    ("psychic", "psychic"): 0.5,
    ("psychic", "dark"): 0.0,
    ("psychic", "steel"): 0.5,
    # Bug
    ("bug", "fire"): 0.5,
    ("bug", "grass"): 2.0,
    ("bug", "fighting"): 0.5,
    ("bug", "flying"): 0.5,
    ("bug", "poison"): 0.5,
    ("bug", "ghost"): 0.5,
    ("bug", "psychic"): 2.0,
    ("bug", "dark"): 2.0,
    ("bug", "steel"): 0.5,
    ("bug", "fairy"): 0.5,
    # Ice
    ("ice", "fire"): 0.5,
    ("ice", "water"): 0.5,
    ("ice", "grass"): 2.0,
    ("ice", "ice"): 0.5,
    ("ice", "ground"): 2.0,
    ("ice", "flying"): 2.0,
    ("ice", "dragon"): 2.0,
    ("ice", "steel"): 0.5,
    # Rock
    ("rock", "fire"): 2.0,
    ("rock", "ice"): 2.0,
    ("rock", "fighting"): 0.5,
    ("rock", "ground"): 0.5,
    ("rock", "flying"): 2.0,
    ("rock", "bug"): 2.0,
    ("rock", "steel"): 0.5,
    # Ghost
    ("ghost", "normal"): 0.0,
    ("ghost", "ghost"): 2.0,
    ("ghost", "psychic"): 2.0,
    ("ghost", "dark"): 0.5,
    # Dragon
    ("dragon", "dragon"): 2.0,
    ("dragon", "steel"): 0.5,
    ("dragon", "fairy"): 0.0,
    # Dark
    ("dark", "fighting"): 0.5,
    ("dark", "ghost"): 2.0,
    ("dark", "psychic"): 2.0,
    ("dark", "dark"): 0.5,
    ("dark", "fairy"): 0.5,
    # Steel
    ("steel", "fire"): 0.5,
    ("steel", "water"): 0.5,
    ("steel", "electric"): 0.5,
    ("steel", "ice"): 2.0,
    ("steel", "rock"): 2.0,
    ("steel", "fairy"): 2.0,
    ("steel", "steel"): 0.5,
    # Fighting
    ("fighting", "normal"): 2.0,
    ("fighting", "ice"): 2.0,
    ("fighting", "rock"): 2.0,
    ("fighting", "dark"): 2.0,
    ("fighting", "steel"): 2.0,
    ("fighting", "poison"): 0.5,
    ("fighting", "flying"): 0.5,
    ("fighting", "psychic"): 0.5,
    ("fighting", "bug"): 0.5,
    ("fighting", "ghost"): 0.0,
    ("fighting", "fairy"): 0.5,
    # Fairy
    ("fairy", "fire"): 0.5,
    ("fairy", "fighting"): 2.0,
    ("fairy", "poison"): 0.5,
    ("fairy", "dragon"): 2.0,
    ("fairy", "dark"): 2.0,
    ("fairy", "steel"): 0.5,
}


def _get_type_effectiveness(move_type: str, defender_types: list[str]) -> float:
    """Calculate type effectiveness multiplier against a list of defender types."""
    multiplier = 1.0
    for def_type in defender_types:
        multiplier *= _TYPE_CHART.get((move_type, def_type), 1.0)
    return multiplier


def _effectiveness_label(multiplier: float) -> str:
    if multiplier == 0.0:
        return "immune"
    elif multiplier > 1.0:
        return "super_effective"
    elif multiplier < 1.0:
        return "not_very_effective"
    return "normal"


def _calculate_damage(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move: Move,
) -> tuple[int, str, bool]:
    """Calculate damage using Gen 1-style formula.

    Returns (damage, effectiveness_label, is_critical).
    """
    if move.power == 0:
        return 0, "normal", False

    # Accuracy check handled by caller

    # Critical hit check (1/16 chance)
    is_critical = random.randint(1, 16) == 1
    crit_modifier = 2.0 if is_critical else 1.0

    # Determine attack/defense stats based on move category (with stat stages)
    md = get_move_data(move.name)
    category = md.get("category", "physical") if md else "physical"
    if category == "special":
        attack_stat = get_effective_stat(attacker, "sp_attack")
        defense_stat = get_effective_stat(defender, "sp_defense")
    else:
        attack_stat = get_effective_stat(attacker, "attack")
        defense_stat = get_effective_stat(defender, "defense")

    # STAB (Same Type Attack Bonus)
    stab = 1.5 if move.type in attacker.types else 1.0

    # Type effectiveness
    type_eff = _get_type_effectiveness(move.type, defender.types)

    # Random factor (0.85 to 1.0)
    random_factor = random.uniform(0.85, 1.0)

    # Gen 1-style damage formula
    level_factor = (2 * attacker.level / 5) + 2
    base_damage = (level_factor * move.power * attack_stat / defense_stat) / 50 + 2
    modifier = stab * type_eff * random_factor * crit_modifier
    damage = max(1, math.floor(base_damage * modifier))

    if type_eff == 0.0:
        damage = 0

    return damage, _effectiveness_label(type_eff), is_critical


def _choose_enemy_move(pokemon: BattlePokemon) -> Move:
    """Simple AI: randomly pick a move with power > 0, or any move."""
    attack_moves = [m for m in pokemon.moves if m.power > 0]
    if attack_moves:
        return random.choice(attack_moves)
    return random.choice(pokemon.moves)


def start_battle(
    player_pokemon_data: dict,
    enemy_pokemon_data: dict,
    battle_type: str = "wild",
) -> BattleState:
    """Initialize a new battle."""
    player_mon = BattlePokemon(**player_pokemon_data)
    enemy_mon = BattlePokemon(**enemy_pokemon_data)

    battle_id = uuid.uuid4().hex[:8]
    battle = BattleState(
        id=battle_id,
        battle_type=battle_type,
        player_pokemon=player_mon,
        enemy_pokemon=enemy_mon,
        can_run=(battle_type == "wild"),
    )
    _battles[battle_id] = battle
    return battle


def get_battle(battle_id: str) -> BattleState | None:
    return _battles.get(battle_id)


def _try_run(player_speed: int, enemy_speed: int) -> bool:
    """Calculate run success probability based on speed comparison."""
    if enemy_speed == 0:
        return True
    odds = (player_speed * 128 // enemy_speed + 30) % 256
    return random.randint(0, 255) < odds


def process_action(
    battle_id: str,
    action: str,
    move_index: int | None = None,
) -> TurnResult | None:
    """Process a player action and resolve the turn."""
    battle = _battles.get(battle_id)
    if battle is None or battle.is_over:
        return None

    events: list[TurnEvent] = []
    battle.turn_count += 1

    # Handle run
    if action == "run":
        if not battle.can_run:
            return TurnResult(
                events=[],
                battle_over=False,
                ran_away=False,
                run_failed=True,
            )
        if _try_run(get_effective_stat(battle.player_pokemon, "speed"), get_effective_stat(battle.enemy_pokemon, "speed")):
            battle.is_over = True
            return TurnResult(events=[], battle_over=True, ran_away=True)
        else:
            # Failed to run — enemy gets a free attack
            enemy_move = _choose_enemy_move(battle.enemy_pokemon)
            if random.randint(1, 100) <= enemy_move.accuracy:
                dmg, eff, crit = _calculate_damage(
                    battle.enemy_pokemon, battle.player_pokemon, enemy_move
                )
                battle.player_pokemon.current_hp = max(
                    0, battle.player_pokemon.current_hp - dmg
                )
                fainted = battle.player_pokemon.current_hp == 0
                events.append(
                    TurnEvent(
                        attacker="enemy",
                        move=enemy_move.name,
                        damage=dmg,
                        effectiveness=eff,
                        critical=crit,
                        target_hp_remaining=battle.player_pokemon.current_hp,
                        target_fainted=fainted,
                    )
                )
                if fainted:
                    battle.is_over = True
                    battle.winner = "enemy"
            return TurnResult(
                events=events,
                battle_over=battle.is_over,
                winner=battle.winner,
                run_failed=True,
            )

    # Handle fight
    if action != "fight" or move_index is None:
        return None

    if move_index < 0 or move_index >= len(battle.player_pokemon.moves):
        return None

    player_move = battle.player_pokemon.moves[move_index]
    enemy_move = _choose_enemy_move(battle.enemy_pokemon)

    status_events: list[StatusEvent] = []

    # Determine turn order by effective speed
    player_speed = get_effective_stat(battle.player_pokemon, "speed")
    enemy_speed = get_effective_stat(battle.enemy_pokemon, "speed")
    player_first = player_speed >= enemy_speed

    if player_first:
        first = ("player", battle.player_pokemon, battle.enemy_pokemon, player_move)
        second = ("enemy", battle.enemy_pokemon, battle.player_pokemon, enemy_move)
    else:
        first = ("enemy", battle.enemy_pokemon, battle.player_pokemon, enemy_move)
        second = ("player", battle.player_pokemon, battle.enemy_pokemon, player_move)

    for role, attacker, defender, move in [first, second]:
        # Skip if attacker already fainted
        if attacker.current_hp <= 0:
            continue

        # Process status effects before move (paralysis, sleep, freeze, confusion)
        can_move, pre_events = process_status_before_move(attacker, role)
        status_events.extend(pre_events)

        # Check if attacker fainted from confusion self-hit
        if attacker.current_hp <= 0:
            battle.is_over = True
            battle.winner = "enemy" if role == "player" else "player"
            break

        if not can_move:
            continue

        # Accuracy check
        if random.randint(1, 100) > move.accuracy:
            events.append(
                TurnEvent(
                    attacker=role,
                    move=move.name,
                    damage=0,
                    effectiveness="normal",
                    critical=False,
                    target_hp_remaining=defender.current_hp,
                    target_fainted=False,
                )
            )
            continue

        dmg, eff, crit = _calculate_damage(attacker, defender, move)

        # Ability: check type immunity (Levitate, Water Absorb, Flash Fire)
        attacker_role = role
        defender_role = "enemy" if role == "player" else "player"
        immune, ab_events = check_ability_type_immunity(defender, move, defender_role)
        status_events.extend(ab_events)
        if immune:
            events.append(
                TurnEvent(
                    attacker=role,
                    move=move.name,
                    damage=0,
                    effectiveness="immune",
                    critical=False,
                    target_hp_remaining=defender.current_hp,
                    target_fainted=False,
                )
            )
            continue

        # Ability: damage modifiers (Overgrow/Blaze/Torrent, Flash Fire boost, Sturdy)
        dmg, ab_dmg_events = process_ability_damage_modifier(
            attacker, defender, move, dmg, attacker_role, defender_role,
        )
        status_events.extend(ab_dmg_events)

        did_damage = dmg > 0
        defender.current_hp = max(0, defender.current_hp - dmg)
        fainted = defender.current_hp == 0

        events.append(
            TurnEvent(
                attacker=role,
                move=move.name,
                damage=dmg,
                effectiveness=eff,
                critical=crit,
                target_hp_remaining=defender.current_hp,
                target_fainted=fainted,
            )
        )

        # Process move secondary effects (status infliction, stat changes)
        if not fainted:
            move_effects = process_move_effects(
                move.name, attacker, defender, attacker_role, defender_role, did_damage
            )
            status_events.extend(move_effects)

            # Ability: on-hit contact abilities (Static, Flame Body, Poison Point)
            if did_damage:
                hit_events = process_ability_on_hit(
                    attacker, defender, move, attacker_role, defender_role,
                )
                status_events.extend(hit_events)

        if fainted:
            battle.is_over = True
            battle.winner = role
            break

    # End-of-turn status damage (poison, burn, toxic)
    if not battle.is_over:
        for role, pokemon in [("player", battle.player_pokemon), ("enemy", battle.enemy_pokemon)]:
            eot_events = process_status_end_of_turn(pokemon, role)
            status_events.extend(eot_events)
            if pokemon.current_hp <= 0:
                battle.is_over = True
                battle.winner = "enemy" if role == "player" else "player"
                break

    # End-of-turn ability effects (Speed Boost, etc.)
    if not battle.is_over:
        for role, pokemon in [("player", battle.player_pokemon), ("enemy", battle.enemy_pokemon)]:
            ab_eot = process_ability_end_of_turn(pokemon, role)
            status_events.extend(ab_eot)

    # Reset flinch at end of turn
    battle.player_pokemon.flinched = False
    battle.enemy_pokemon.flinched = False

    battle.log.extend([e.model_dump() for e in events])

    return TurnResult(
        events=events,
        status_events=status_events,
        battle_over=battle.is_over,
        winner=battle.winner,
    )
