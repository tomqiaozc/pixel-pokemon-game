from __future__ import annotations

import random

from ..models.ai import AIDecision
from ..models.battle import BattlePokemon
from ..models.pokemon import Move
from .battle_service import _get_type_effectiveness, get_battle
from .encounter_service import get_move_data


def _move_score(move: Move, attacker: BattlePokemon, defender: BattlePokemon) -> float:
    """Score a move based on effectiveness, power, STAB, and accuracy."""
    if move.power == 0:
        return 0.0

    type_eff = _get_type_effectiveness(move.type, defender.types)
    if type_eff == 0.0:
        return -100.0  # never pick immune moves

    stab = 1.5 if move.type in attacker.types else 1.0

    # Use move category to pick correct stats
    md = get_move_data(move.name)
    category = md.get("category", "physical") if md else "physical"
    if category == "special":
        atk = attacker.stats.sp_attack
        dfn = defender.stats.sp_defense
    else:
        atk = attacker.stats.attack
        dfn = defender.stats.defense

    # Estimated damage (simplified)
    level_factor = (2 * attacker.level / 5) + 2
    base_dmg = (level_factor * move.power * atk / max(dfn, 1)) / 50 + 2
    estimated = base_dmg * stab * type_eff * (move.accuracy / 100.0)
    return estimated


def _choose_easy(enemy: BattlePokemon, player: BattlePokemon) -> AIDecision:
    """Wild Pokemon AI: random move selection."""
    valid_moves = [i for i, m in enumerate(enemy.moves) if m.power > 0]
    if not valid_moves:
        valid_moves = list(range(len(enemy.moves)))
    idx = random.choice(valid_moves)
    return AIDecision(
        action_type="fight",
        move_index=idx,
        reasoning=f"Random move: {enemy.moves[idx].name}",
    )


def _choose_normal(enemy: BattlePokemon, player: BattlePokemon) -> AIDecision:
    """Basic trainer AI with heuristics."""
    best_idx = 0
    best_score = -999.0

    player_low_hp = player.current_hp < player.max_hp * 0.25

    for i, move in enumerate(enemy.moves):
        score = _move_score(move, enemy, player)

        # If player is low HP, prefer damaging moves over status
        if player_low_hp and move.power == 0:
            score -= 50.0

        if score > best_score:
            best_score = score
            best_idx = i

    # Fallback: if best score is still very low (all status moves), pick first attack
    if best_score <= 0:
        for i, move in enumerate(enemy.moves):
            if move.power > 0:
                best_idx = i
                break

    chosen = enemy.moves[best_idx]
    reasoning = f"Chose {chosen.name}"
    if best_score > 0:
        type_eff = _get_type_effectiveness(chosen.type, player.types)
        if type_eff > 1.0:
            reasoning += " (super effective)"
        elif chosen.type in enemy.types:
            reasoning += " (STAB)"

    return AIDecision(
        action_type="fight",
        move_index=best_idx,
        reasoning=reasoning,
    )


def _choose_hard(enemy: BattlePokemon, player: BattlePokemon) -> AIDecision:
    """Gym leader AI: smarter move selection with STAB priority."""
    best_idx = 0
    best_score = -999.0

    player_low_hp = player.current_hp < player.max_hp * 0.25

    for i, move in enumerate(enemy.moves):
        score = _move_score(move, enemy, player)

        # Only give STAB bonus when not fighting a type disadvantage
        type_eff = _get_type_effectiveness(move.type, player.types)
        if move.type in enemy.types and move.power > 0 and type_eff >= 1.0:
            score += 5.0

        # Penalize status moves when enemy can KO
        if player_low_hp and move.power == 0:
            score -= 100.0

        # Prefer higher accuracy moves when player is low
        if player_low_hp and move.power > 0:
            score += move.accuracy * 0.1

        if score > best_score:
            best_score = score
            best_idx = i

    # Fallback
    if best_score <= 0:
        for i, move in enumerate(enemy.moves):
            if move.power > 0:
                best_idx = i
                break

    chosen = enemy.moves[best_idx]
    reasoning = f"Leader chose {chosen.name}"
    type_eff = _get_type_effectiveness(chosen.type, player.types)
    if type_eff > 1.0:
        reasoning += " (super effective)"
    if chosen.type in enemy.types and chosen.power > 0:
        reasoning += " (STAB)"

    return AIDecision(
        action_type="fight",
        move_index=best_idx,
        reasoning=reasoning,
    )


def get_ai_action(battle_id: str, difficulty: str = "normal") -> AIDecision | None:
    """Get an AI decision for the enemy Pokemon in a battle."""
    battle = get_battle(battle_id)
    if battle is None or battle.is_over:
        return None

    enemy = battle.enemy_pokemon
    player = battle.player_pokemon

    if not enemy.moves:
        return None

    if difficulty == "easy":
        return _choose_easy(enemy, player)
    elif difficulty == "hard":
        return _choose_hard(enemy, player)
    else:
        return _choose_normal(enemy, player)
