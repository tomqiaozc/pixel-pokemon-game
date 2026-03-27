from __future__ import annotations

import math
from typing import Optional

from ..models.evolution import (
    EvolutionCheckResponse,
    EvolutionResult,
    LevelUpResult,
)
from ..models.pokemon import Move
from .encounter_service import (
    _calc_stat,
    _generate_moves_for_level,
    get_move_data,
    get_species,
)
from .game_service import get_game, _games


# EXP thresholds per level (simplified medium-fast growth rate)
def _exp_for_level(level: int) -> int:
    """Calculate total EXP needed to reach a given level (medium-fast curve)."""
    return level ** 3


def _level_from_exp(total_exp: int) -> int:
    """Calculate level from total EXP."""
    level = 1
    while _exp_for_level(level + 1) <= total_exp and level < 100:
        level += 1
    return level


def check_evolution(species_id: int, current_level: int) -> EvolutionCheckResponse:
    """Check if a Pokemon can evolve at its current level."""
    species = get_species(species_id)
    if species is None or species.evolution is None:
        return EvolutionCheckResponse(can_evolve=False)

    can = current_level >= species.evolution.level
    target = get_species(species.evolution.to)
    return EvolutionCheckResponse(
        can_evolve=can,
        evolves_to=species.evolution.to if can else None,
        evolves_to_name=target.name if can and target else None,
        evolution_level=species.evolution.level,
    )


def evolve_pokemon(pokemon_data: dict) -> Optional[EvolutionResult]:
    """Execute evolution on a Pokemon dict, returning the evolved form."""
    species = get_species(pokemon_data["id"])
    if species is None or species.evolution is None:
        return None

    level = pokemon_data["level"]
    if level < species.evolution.level:
        return None

    new_species = get_species(species.evolution.to)
    if new_species is None:
        return None

    # Recalculate stats with new base stats (keeping same IVs approximation)
    # Since we don't store IVs directly, use mid-range IVs (15)
    iv = 15
    new_hp = _calc_stat(new_species.stats.hp, level, iv, is_hp=True)
    new_stats = {
        "hp": new_hp,
        "attack": _calc_stat(new_species.stats.attack, level, iv),
        "defense": _calc_stat(new_species.stats.defense, level, iv),
        "sp_attack": _calc_stat(new_species.stats.sp_attack, level, iv),
        "sp_defense": _calc_stat(new_species.stats.sp_defense, level, iv),
        "speed": _calc_stat(new_species.stats.speed, level, iv),
    }

    new_moves = _generate_moves_for_level(new_species, level)

    return EvolutionResult(
        success=True,
        old_species_id=species.id,
        old_name=species.name,
        new_species_id=new_species.id,
        new_name=new_species.name,
        new_stats=new_stats,
        new_moves=new_moves,
        new_level=level,
    )


def get_pending_moves(species_id: int, current_level: int, current_moves: list[dict]) -> list[dict]:
    """Get moves available at the current level that aren't already known."""
    species = get_species(species_id)
    if species is None:
        return []

    current_names = {m["name"] for m in current_moves}
    pending = []
    for entry in species.learnset:
        if entry.level == current_level and entry.move not in current_names:
            md = get_move_data(entry.move)
            if md:
                pending.append(md)
            else:
                pending.append({"name": entry.move, "type": "normal", "power": 0, "accuracy": 100, "pp": 20})
    return pending


def award_exp(
    game_id: str,
    pokemon_index: int,
    defeated_species_id: int,
    defeated_level: int,
) -> Optional[LevelUpResult]:
    """Award EXP to a Pokemon after defeating an enemy."""
    game = get_game(game_id)
    if game is None:
        return None

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        return None

    pokemon = team[pokemon_index]
    defeated_species = get_species(defeated_species_id)
    if defeated_species is None:
        return None

    # EXP formula: (base_exp * defeated_level) / 7
    exp_gained = max(1, (defeated_species.base_exp * defeated_level) // 7)

    old_level = pokemon["level"]
    current_exp = pokemon.get("exp", _exp_for_level(old_level))
    new_total_exp = current_exp + exp_gained
    new_level = _level_from_exp(new_total_exp)

    # Cap at 100
    new_level = min(new_level, 100)

    leveled_up = new_level > old_level

    # Check for new moves at each level gained
    new_moves: list[str] = []
    if leveled_up:
        species = get_species(pokemon["id"])
        if species:
            for lvl in range(old_level + 1, new_level + 1):
                for entry in species.learnset:
                    if entry.level == lvl:
                        new_moves.append(entry.move)

    # Check evolution
    can_evolve = False
    if leveled_up:
        evo_check = check_evolution(pokemon["id"], new_level)
        can_evolve = evo_check.can_evolve

    # Update Pokemon in game state
    pokemon["level"] = new_level
    pokemon["exp"] = new_total_exp

    # Recalculate stats if leveled up
    new_stats = None
    if leveled_up:
        species = get_species(pokemon["id"])
        if species:
            iv = 15  # mid-range approximation
            hp = _calc_stat(species.stats.hp, new_level, iv, is_hp=True)
            pokemon["stats"] = {
                "hp": hp,
                "attack": _calc_stat(species.stats.attack, new_level, iv),
                "defense": _calc_stat(species.stats.defense, new_level, iv),
                "sp_attack": _calc_stat(species.stats.sp_attack, new_level, iv),
                "sp_defense": _calc_stat(species.stats.sp_defense, new_level, iv),
                "speed": _calc_stat(species.stats.speed, new_level, iv),
            }
            new_stats = pokemon["stats"]

    return LevelUpResult(
        exp_gained=exp_gained,
        new_total_exp=new_total_exp,
        leveled_up=leveled_up,
        old_level=old_level,
        new_level=new_level,
        can_evolve=can_evolve,
        new_moves=new_moves,
        new_stats=new_stats,
    )
