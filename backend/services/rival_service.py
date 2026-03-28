"""Rival trainer system — init, team scaling, and battle management."""
from __future__ import annotations

import random
from typing import Optional

from ..models.quest import RivalBattleResult, RivalData, RivalPokemon
from .battle_service import start_battle
from .encounter_service import _calc_stat, _generate_moves_for_level, get_species
from .quest_service import check_quest_progress, set_story_flag

# In-memory rival state per game
_rival_data: dict[str, RivalData] = {}

# Starter counter mapping: player_starter_id -> rival_starter_id
_COUNTER_STARTERS = {
    1: 4,   # player Bulbasaur -> rival Charmander
    4: 7,   # player Charmander -> rival Squirtle
    7: 1,   # player Squirtle -> rival Bulbasaur
}

# Evolution chains for starters
_STARTER_CHAINS = {
    1: [1, 2, 3],     # Bulbasaur -> Ivysaur -> Venusaur
    4: [4, 5, 6],     # Charmander -> Charmeleon -> Charizard
    7: [7, 8, 9],     # Squirtle -> Wartortle -> Blastoise
}

# Rival team templates by encounter stage
# Each stage defines: [(species_id, level)] — "starter" uses rival's evolved starter
_RIVAL_TEAMS: dict[int, list[tuple[str | int, int]]] = {
    # Stage 1: Oak's Lab — just the starter
    1: [("starter", 5)],
    # Stage 2: Route 2 — evolved starter + Pidgeotto
    2: [("starter", 15), (11, 14)],
    # Stage 3: Pre-Elite Four — full competitive team
    3: [("starter", 50), (12, 47), (15, 47), (18, 45), (14, 45), (17, 45)],
}


def _get_rival(game_id: str) -> RivalData:
    if game_id not in _rival_data:
        _rival_data[game_id] = RivalData()
    return _rival_data[game_id]


def init_rival(game_id: str, player_starter_id: int) -> RivalData:
    """Initialize the rival based on the player's starter choice."""
    rival_starter = _COUNTER_STARTERS.get(player_starter_id, 4)
    rival = RivalData(
        name="Blue",
        starter_species_id=rival_starter,
        encounter_stage=0,
        current_team=[],
    )
    _rival_data[game_id] = rival
    return rival


def get_rival(game_id: str) -> RivalData:
    """Return current rival data."""
    return _get_rival(game_id)


def _get_evolved_starter(base_starter_id: int, level: int) -> int:
    """Return the appropriate evolution for the starter at the given level."""
    chain = _STARTER_CHAINS.get(base_starter_id, [base_starter_id])
    # Walk the chain forward: find the highest evolution the level qualifies for
    current_id = chain[0]
    for species_id in chain:
        species = get_species(species_id)
        if species is None:
            break
        current_id = species_id
        evo = species.evolution
        if evo is None:
            break  # final form
        if level < evo.level:
            break  # not high enough level to evolve further
        # Level is enough — continue to next evolution
    return current_id


def _build_rival_pokemon(species_id: int, level: int) -> RivalPokemon:
    """Build a RivalPokemon with calculated stats and level-appropriate moves."""
    species = get_species(species_id)
    if species is None:
        raise ValueError(f"Species {species_id} not found")

    moves = _generate_moves_for_level(species, level)
    return RivalPokemon(
        species_id=species_id,
        name=species.name,
        level=level,
        moves=[m.name for m in moves],
    )


def build_rival_team(game_id: str, stage: int) -> list[RivalPokemon]:
    """Build the rival's team for a given encounter stage."""
    rival = _get_rival(game_id)
    template = _RIVAL_TEAMS.get(stage, _RIVAL_TEAMS[1])

    team: list[RivalPokemon] = []
    for entry_id, level in template:
        if entry_id == "starter":
            species_id = _get_evolved_starter(rival.starter_species_id, level)
        else:
            species_id = entry_id
        team.append(_build_rival_pokemon(species_id, level))

    rival.current_team = team
    rival.encounter_stage = stage
    return team


def _rival_pokemon_to_battle_dict(rpoke: RivalPokemon) -> dict:
    """Convert a RivalPokemon to a dict suitable for BattlePokemon / start_battle."""
    species = get_species(rpoke.species_id)
    if species is None:
        raise ValueError(f"Species {rpoke.species_id} not found")

    # Use fixed decent IVs for rival (20 across the board)
    iv = 20
    hp = _calc_stat(species.stats.hp, rpoke.level, iv, is_hp=True)
    stats = {
        "hp": hp,
        "attack": _calc_stat(species.stats.attack, rpoke.level, iv),
        "defense": _calc_stat(species.stats.defense, rpoke.level, iv),
        "sp_attack": _calc_stat(species.stats.sp_attack, rpoke.level, iv),
        "sp_defense": _calc_stat(species.stats.sp_defense, rpoke.level, iv),
        "speed": _calc_stat(species.stats.speed, rpoke.level, iv),
    }

    moves = _generate_moves_for_level(species, rpoke.level)
    move_dicts = [m.model_dump() for m in moves]

    ability_id = species.abilities[0] if species.abilities else None

    return {
        "species_id": rpoke.species_id,
        "name": rpoke.name,
        "types": species.types,
        "level": rpoke.level,
        "stats": stats,
        "current_hp": hp,
        "max_hp": hp,
        "moves": move_dicts,
        "sprite": species.sprite,
        "ability_id": ability_id,
    }


def start_rival_battle(
    game_id: str, stage: int, player_pokemon_data: dict
) -> Optional[RivalBattleResult]:
    """Start a rival battle at the given encounter stage."""
    rival = _get_rival(game_id)
    team = build_rival_team(game_id, stage)

    if not team:
        return None

    # Use the rival's lead Pokemon for the battle
    lead = team[0]
    enemy_data = _rival_pokemon_to_battle_dict(lead)

    battle = start_battle(player_pokemon_data, enemy_data, battle_type="trainer")

    reward_money = stage * 500 + 500  # 1000, 1500, 2000

    return RivalBattleResult(
        battle_id=battle.id,
        rival_name=rival.name,
        rival_team_preview=[p.name for p in team],
        reward_money=reward_money,
    )


def complete_rival_battle(game_id: str, stage: int) -> None:
    """Called after the player wins a rival battle — set flags and advance quest."""
    rival = _get_rival(game_id)

    # Set story flag for this encounter
    stage_flags = {
        1: "rival_defeated_lab",
        2: "rival_defeated_route2",
        3: "rival_defeated_elite",
    }
    flag = stage_flags.get(stage)
    if flag:
        set_story_flag(game_id, flag)

    # Advance quest progress if applicable
    stage_targets = {
        2: "rival_route2",
    }
    target = stage_targets.get(stage)
    if target:
        check_quest_progress(game_id, "defeat_trainer", {"trainer_id": target})
