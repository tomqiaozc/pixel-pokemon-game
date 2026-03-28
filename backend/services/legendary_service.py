"""Legendary Pokemon encounter system — one-time encounters with story flag gating."""
from __future__ import annotations

from typing import Optional

from ..models.legendary import (
    LegendaryCheckResponse,
    LegendaryDef,
    LegendaryEncounterResponse,
    LegendaryListEntry,
    LegendaryStatus,
)
from ..models.pokemon import Move, Stats
from .battle_service import start_battle
from .encounter_service import _calc_stat, get_move_data
from .game_service import get_game
from .quest_service import get_story_flag

# In-memory legendary status per game
_legendary_status: dict[str, dict[int, LegendaryStatus]] = {}

# --- Legendary definitions ---
LEGENDARY_DEFS: dict[int, LegendaryDef] = {
    150: LegendaryDef(
        species_id=150,
        name="Mewtwo",
        types=["psychic"],
        level=70,
        base_stats={"hp": 106, "attack": 110, "defense": 90, "sp_attack": 154, "sp_defense": 90, "speed": 130},
        catch_rate=3,
        moves=["Psychic", "Recover", "Barrier", "Swift"],
        location="cerulean_cave",
        location_name="Cerulean Cave",
        required_flags=["badge_boulder", "badge_cascade"],
        sprite="mewtwo.png",
        ability="pressure",
    ),
    144: LegendaryDef(
        species_id=144,
        name="Articuno",
        types=["ice", "flying"],
        level=50,
        base_stats={"hp": 90, "attack": 85, "defense": 100, "sp_attack": 95, "sp_defense": 125, "speed": 85},
        catch_rate=3,
        moves=["Ice Beam", "Blizzard", "Agility", "Mist"],
        location="seafoam_islands",
        location_name="Seafoam Islands",
        required_flags=["badge_cascade"],
        sprite="articuno.png",
        ability="pressure",
    ),
    145: LegendaryDef(
        species_id=145,
        name="Zapdos",
        types=["electric", "flying"],
        level=50,
        base_stats={"hp": 90, "attack": 90, "defense": 85, "sp_attack": 125, "sp_defense": 90, "speed": 100},
        catch_rate=3,
        moves=["Thunderbolt", "Thunder", "Agility", "Drill Peck"],
        location="power_plant",
        location_name="Power Plant",
        required_flags=["badge_cascade"],
        sprite="zapdos.png",
        ability="pressure",
    ),
}


def _get_statuses(game_id: str) -> dict[int, LegendaryStatus]:
    if game_id not in _legendary_status:
        _legendary_status[game_id] = {
            sid: LegendaryStatus(species_id=sid) for sid in LEGENDARY_DEFS
        }
    return _legendary_status[game_id]


def _check_flags(game_id: str, required_flags: list[str]) -> tuple[bool, list[str]]:
    """Check if all required flags are set. Returns (all_met, missing_flags)."""
    missing = [f for f in required_flags if not get_story_flag(game_id, f)]
    return len(missing) == 0, missing


def get_all_legendaries(game_id: str) -> list[LegendaryListEntry]:
    """Return all legendaries with current status for the player."""
    statuses = _get_statuses(game_id)
    result = []
    for sid, ldef in LEGENDARY_DEFS.items():
        status = statuses[sid]
        reqs_met, _ = _check_flags(game_id, ldef.required_flags)

        display_status = status.status
        if status.status == "available" and not reqs_met:
            display_status = "locked"

        result.append(LegendaryListEntry(
            species_id=ldef.species_id,
            name=ldef.name,
            types=ldef.types,
            level=ldef.level,
            location=ldef.location,
            location_name=ldef.location_name,
            status=display_status,
            requirements_met=reqs_met,
        ))
    return result


def check_legendary(game_id: str, species_id: int) -> Optional[LegendaryCheckResponse]:
    """Check availability of a specific legendary."""
    ldef = LEGENDARY_DEFS.get(species_id)
    if ldef is None:
        return None

    statuses = _get_statuses(game_id)
    status = statuses[species_id]
    reqs_met, missing = _check_flags(game_id, ldef.required_flags)

    return LegendaryCheckResponse(
        species_id=ldef.species_id,
        name=ldef.name,
        available=status.status == "available" and reqs_met,
        location=ldef.location,
        location_name=ldef.location_name,
        requirements_met=reqs_met,
        already_caught=status.status == "caught",
        already_fainted=status.status == "fainted",
        required_flags=ldef.required_flags,
        missing_flags=missing,
    )


def _build_legendary_battle_dict(ldef: LegendaryDef) -> dict:
    """Build a battle-ready dict for a legendary Pokemon."""
    # Use fixed IVs of 31 for legendaries (max)
    iv = 31
    hp = _calc_stat(ldef.base_stats["hp"], ldef.level, iv, is_hp=True)
    stats = {
        "hp": hp,
        "attack": _calc_stat(ldef.base_stats["attack"], ldef.level, iv),
        "defense": _calc_stat(ldef.base_stats["defense"], ldef.level, iv),
        "sp_attack": _calc_stat(ldef.base_stats["sp_attack"], ldef.level, iv),
        "sp_defense": _calc_stat(ldef.base_stats["sp_defense"], ldef.level, iv),
        "speed": _calc_stat(ldef.base_stats["speed"], ldef.level, iv),
    }

    # Build moves
    moves = []
    for move_name in ldef.moves:
        md = get_move_data(move_name)
        if md:
            moves.append(md)
        else:
            moves.append({"name": move_name, "type": "normal", "power": 0, "accuracy": 100, "pp": 20, "contact": False})

    return {
        "species_id": ldef.species_id,
        "name": ldef.name,
        "types": ldef.types,
        "level": ldef.level,
        "stats": stats,
        "current_hp": hp,
        "max_hp": hp,
        "moves": moves,
        "sprite": ldef.sprite,
        "ability_id": ldef.ability,
        "catch_rate": ldef.catch_rate,
    }


def start_legendary_encounter(
    game_id: str, species_id: int
) -> Optional[LegendaryEncounterResponse]:
    """Start a legendary battle. Validates requirements and one-time status."""
    ldef = LEGENDARY_DEFS.get(species_id)
    if ldef is None:
        return None

    game = get_game(game_id)
    if game is None:
        return None

    statuses = _get_statuses(game_id)
    status = statuses[species_id]

    # Check availability
    if status.status == "caught":
        return None
    if status.status == "fainted":
        return None
    if status.status == "in_battle":
        return None

    # Check requirements
    reqs_met, _ = _check_flags(game_id, ldef.required_flags)
    if not reqs_met:
        return None

    # Build player's lead Pokemon
    player_team = game["player"]["team"]
    if not player_team:
        return None

    lead = player_team[0]
    player_pokemon = {
        "species_id": lead["id"],
        "name": lead["name"],
        "types": lead["types"],
        "level": lead["level"],
        "stats": lead["stats"],
        "current_hp": lead.get("current_hp", lead["stats"]["hp"]),
        "max_hp": lead.get("max_hp", lead["stats"]["hp"]),
        "moves": lead["moves"],
        "sprite": lead["sprite"],
        "ability_id": lead.get("ability_id"),
    }

    # Build legendary
    enemy_data = _build_legendary_battle_dict(ldef)

    # Start battle as wild (so player can catch)
    battle = start_battle(player_pokemon, enemy_data, battle_type="wild")

    # Mark as in_battle
    status.status = "in_battle"

    return LegendaryEncounterResponse(
        battle_id=battle.id,
        legendary_name=ldef.name,
        legendary_level=ldef.level,
        message=f"A wild {ldef.name} appeared!",
    )


def mark_legendary_caught(game_id: str, species_id: int) -> None:
    """Mark a legendary as caught (called after successful catch)."""
    statuses = _get_statuses(game_id)
    if species_id in statuses:
        statuses[species_id].status = "caught"


def mark_legendary_fainted(game_id: str, species_id: int) -> None:
    """Mark a legendary as fainted — permanently unavailable."""
    statuses = _get_statuses(game_id)
    if species_id in statuses:
        statuses[species_id].status = "fainted"


def mark_legendary_fled(game_id: str, species_id: int) -> None:
    """Player ran or whited out — legendary returns to available."""
    statuses = _get_statuses(game_id)
    if species_id in statuses:
        statuses[species_id].status = "available"
