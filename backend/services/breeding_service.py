"""Pokemon breeding and daycare service."""
from __future__ import annotations

import random
import time
from typing import Optional

from ..models.breeding import (
    DaycareSlot,
    DaycareState,
    DaycareStatusResponse,
    EggData,
    HatchResult,
)
from .encounter_service import get_species, _generate_gender
from .game_service import get_game

# In-memory state
_daycares: dict[str, DaycareState] = {}
_eggs: dict[str, list[EggData]] = {}  # game_id -> list of eggs in party

# Breeding constants
EGG_CHECK_STEPS = 256  # check for egg every N steps
BASE_EGG_CHANCE = 0.5  # 50% chance per check when compatible
DEFAULT_HATCH_STEPS = 5000
DAYCARE_EXP_PER_STEP = 1

# Undiscovered egg group — cannot breed
UNDISCOVERED = "undiscovered"
DITTO_GROUP = "ditto"


def _get_daycare(game_id: str) -> DaycareState:
    if game_id not in _daycares:
        _daycares[game_id] = DaycareState()
    return _daycares[game_id]


def _get_egg_group(pokemon: dict) -> list[str]:
    """Get egg groups for a pokemon by looking up species data."""
    species_id = pokemon.get("id", pokemon.get("species_id"))
    if species_id is None:
        return []
    species = get_species(species_id)
    if species is None:
        return []
    return species.egg_groups


def _is_ditto(pokemon: dict) -> bool:
    """Check if a pokemon is Ditto."""
    return pokemon.get("name", "").lower() == "ditto" or DITTO_GROUP in _get_egg_group(pokemon)


def check_compatibility(pokemon_a: dict, pokemon_b: dict) -> tuple[bool, str]:
    """Check if two Pokemon can breed. Returns (compatible, message)."""
    if pokemon_a is None or pokemon_b is None:
        return False, "Need two Pokemon in the daycare"

    groups_a = _get_egg_group(pokemon_a)
    groups_b = _get_egg_group(pokemon_b)

    # Undiscovered cannot breed
    if UNDISCOVERED in groups_a or UNDISCOVERED in groups_b:
        return False, "One or both Pokemon cannot breed"

    # Two Dittos cannot breed
    if _is_ditto(pokemon_a) and _is_ditto(pokemon_b):
        return False, "Two Ditto cannot breed with each other"

    # Ditto breeds with anything (except undiscovered/ditto)
    if _is_ditto(pokemon_a) or _is_ditto(pokemon_b):
        return True, "The two seem to get along"

    # Check gender compatibility
    gender_a = pokemon_a.get("gender")
    gender_b = pokemon_b.get("gender")
    if gender_a == gender_b:
        if gender_a is not None:
            return False, "The two prefer to play with others"
    if gender_a is None and gender_b is None:
        return False, "The two prefer to play with others"

    # Check egg group overlap
    shared = set(groups_a) & set(groups_b)
    if not shared:
        return False, "The two don't seem to like each other"

    return True, "The two seem to get along"


def _determine_offspring_species(parent_a: dict, parent_b: dict) -> int:
    """Determine offspring species. Mother's species (or non-Ditto parent)."""
    if _is_ditto(parent_a) and not _is_ditto(parent_b):
        return parent_b.get("id", parent_b.get("species_id", 1))
    if _is_ditto(parent_b) and not _is_ditto(parent_a):
        return parent_a.get("id", parent_a.get("species_id", 1))

    # If neither is Ditto, use the female parent
    if parent_a.get("gender") == "female":
        return parent_a.get("id", parent_a.get("species_id", 1))
    if parent_b.get("gender") == "female":
        return parent_b.get("id", parent_b.get("species_id", 1))

    # Fallback: first parent
    return parent_a.get("id", parent_a.get("species_id", 1))


def _inherit_ivs(parent_a: dict, parent_b: dict) -> dict:
    """Inherit 3 random IVs from parents, rest are random."""
    stats = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]
    ivs_a = parent_a.get("ivs", {stat: random.randint(0, 31) for stat in stats})
    ivs_b = parent_b.get("ivs", {stat: random.randint(0, 31) for stat in stats})

    # Pick 3 random stats to inherit from parents
    inherited_stats = random.sample(stats, 3)
    result = {}
    for stat in stats:
        if stat in inherited_stats:
            # Randomly pick from either parent
            result[stat] = random.choice([ivs_a.get(stat, 0), ivs_b.get(stat, 0)])
        else:
            result[stat] = random.randint(0, 31)
    return result


def _get_egg_moves(father: dict, species_id: int) -> list[dict]:
    """Get egg moves from father's moveset. For simplicity, inherit first move."""
    species = get_species(species_id)
    if species is None:
        return [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}]

    # Inherit up to 1 move from father if it's a valid move
    father_moves = father.get("moves", [])
    egg_moves = []
    if father_moves:
        egg_moves.append(father_moves[0])

    # Fill with default moves for the species at level 1
    if not egg_moves:
        egg_moves = [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}]

    return egg_moves[:4]


def _identify_father(parent_a: dict, parent_b: dict) -> dict:
    """Identify the father for egg move inheritance."""
    if _is_ditto(parent_a):
        return parent_b  # Ditto is never the father for move inheritance
    if _is_ditto(parent_b):
        return parent_a
    if parent_a.get("gender") == "male":
        return parent_a
    return parent_b


def generate_egg(parent_a: dict, parent_b: dict) -> EggData:
    """Generate an egg from two compatible parents."""
    species_id = _determine_offspring_species(parent_a, parent_b)
    species = get_species(species_id)

    ivs = _inherit_ivs(parent_a, parent_b)
    father = _identify_father(parent_a, parent_b)
    moves = _get_egg_moves(father, species_id)

    gender = None
    if species:
        gender = _generate_gender(species)

    name = species.name if species else "Unknown"
    types = species.types if species else ["normal"]
    base_stats = None
    if species:
        base_stats = {
            "hp": species.stats.hp,
            "attack": species.stats.attack,
            "defense": species.stats.defense,
            "sp_attack": species.stats.sp_attack,
            "sp_defense": species.stats.sp_defense,
            "speed": species.stats.speed,
        }

    return EggData(
        species_id=species_id,
        name=name,
        ivs=ivs,
        moves=moves,
        gender=gender,
        hatch_counter=DEFAULT_HATCH_STEPS,
        types=types,
        base_stats=base_stats,
    )


# --- Public API ---

def deposit_pokemon(game_id: str, pokemon_index: int) -> DaycareStatusResponse:
    """Deposit a Pokemon from the player's team into the daycare."""
    game = get_game(game_id)
    if game is None:
        raise ValueError("Game not found")

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        raise ValueError("Invalid Pokemon index")

    if len(team) <= 1:
        raise ValueError("Cannot deposit last Pokemon")

    daycare = _get_daycare(game_id)

    if daycare.slot_1 is not None and daycare.slot_2 is not None:
        raise ValueError("Daycare is full")

    pokemon = team.pop(pokemon_index)
    slot = DaycareSlot(pokemon=pokemon, deposited_at=time.time())

    if daycare.slot_1 is None:
        daycare.slot_1 = slot
    else:
        daycare.slot_2 = slot

    # Reset egg state when depositing
    daycare.egg_ready = False
    daycare.egg_steps_accumulated = 0

    return get_daycare_status(game_id)


def withdraw_pokemon(game_id: str, slot: int) -> DaycareStatusResponse:
    """Withdraw a Pokemon from the daycare back to the player's team."""
    game = get_game(game_id)
    if game is None:
        raise ValueError("Game not found")

    daycare = _get_daycare(game_id)

    if slot == 1 and daycare.slot_1 is not None:
        pokemon = daycare.slot_1.pokemon
        daycare.slot_1 = None
    elif slot == 2 and daycare.slot_2 is not None:
        pokemon = daycare.slot_2.pokemon
        daycare.slot_2 = None
    else:
        raise ValueError("No Pokemon in that slot")

    team = game["player"]["team"]
    if len(team) >= 6:
        raise ValueError("Team is full")

    team.append(pokemon)

    # Reset egg state
    daycare.egg_ready = False
    daycare.egg_steps_accumulated = 0

    return get_daycare_status(game_id)


def get_daycare_status(game_id: str) -> DaycareStatusResponse:
    """Get current daycare status."""
    daycare = _get_daycare(game_id)

    slot_1_data = None
    slot_2_data = None
    if daycare.slot_1:
        slot_1_data = {
            "name": daycare.slot_1.pokemon.get("name", "Unknown"),
            "level": daycare.slot_1.pokemon.get("level", 1),
            "species_id": daycare.slot_1.pokemon.get("id", daycare.slot_1.pokemon.get("species_id")),
            "sprite": daycare.slot_1.pokemon.get("sprite", "unknown.png"),
            "steps_gained": daycare.slot_1.steps_gained,
        }
    if daycare.slot_2:
        slot_2_data = {
            "name": daycare.slot_2.pokemon.get("name", "Unknown"),
            "level": daycare.slot_2.pokemon.get("level", 1),
            "species_id": daycare.slot_2.pokemon.get("id", daycare.slot_2.pokemon.get("species_id")),
            "sprite": daycare.slot_2.pokemon.get("sprite", "unknown.png"),
            "steps_gained": daycare.slot_2.steps_gained,
        }

    compatible = False
    compat_msg = ""
    if daycare.slot_1 and daycare.slot_2:
        compatible, compat_msg = check_compatibility(
            daycare.slot_1.pokemon, daycare.slot_2.pokemon
        )
    else:
        compat_msg = "Need two Pokemon in the daycare"

    return DaycareStatusResponse(
        slot_1=slot_1_data,
        slot_2=slot_2_data,
        egg_ready=daycare.egg_ready,
        compatible=compatible,
        compatibility_message=compat_msg,
    )


def process_steps(game_id: str, steps: int) -> HatchResult:
    """Process steps for daycare EXP, egg generation, and egg hatching."""
    if steps <= 0:
        return HatchResult(message="No steps taken")

    daycare = _get_daycare(game_id)

    # Give EXP to deposited Pokemon
    if daycare.slot_1:
        daycare.slot_1.steps_gained += steps
    if daycare.slot_2:
        daycare.slot_2.steps_gained += steps

    # Check for egg generation
    if not daycare.egg_ready and daycare.slot_1 and daycare.slot_2:
        compatible, _ = check_compatibility(
            daycare.slot_1.pokemon, daycare.slot_2.pokemon
        )
        if compatible:
            daycare.egg_steps_accumulated += steps
            while daycare.egg_steps_accumulated >= EGG_CHECK_STEPS:
                daycare.egg_steps_accumulated -= EGG_CHECK_STEPS
                if random.random() < BASE_EGG_CHANCE:
                    daycare.egg_ready = True
                    break

    # Check for egg hatching in party
    game = get_game(game_id)
    if game is None:
        return HatchResult(message="Steps processed")

    team = game["player"]["team"]
    for i, pokemon in enumerate(team):
        if pokemon.get("is_egg"):
            hatch_counter = pokemon.get("hatch_counter", DEFAULT_HATCH_STEPS)
            hatch_counter -= steps
            if hatch_counter <= 0:
                # Hatch the egg!
                hatched = _hatch_egg(pokemon)
                team[i] = hatched
                return HatchResult(
                    hatched=True,
                    pokemon=hatched,
                    message=f"Oh? Your egg hatched into {hatched['name']}!",
                )
            else:
                pokemon["hatch_counter"] = hatch_counter

    return HatchResult(message="Steps processed")


def _hatch_egg(egg: dict) -> dict:
    """Convert an egg into a hatched Pokemon."""
    from .encounter_service import _calc_stat

    ivs = egg.get("ivs", {})
    base_stats = egg.get("base_stats", {
        "hp": 45, "attack": 49, "defense": 49,
        "sp_attack": 65, "sp_defense": 65, "speed": 45
    })
    level = 1

    hp = _calc_stat(base_stats.get("hp", 45), level, ivs.get("hp", 0), is_hp=True)
    stats = {
        "hp": hp,
        "attack": _calc_stat(base_stats.get("attack", 49), level, ivs.get("attack", 0)),
        "defense": _calc_stat(base_stats.get("defense", 49), level, ivs.get("defense", 0)),
        "sp_attack": _calc_stat(base_stats.get("sp_attack", 65), level, ivs.get("sp_attack", 0)),
        "sp_defense": _calc_stat(base_stats.get("sp_defense", 65), level, ivs.get("sp_defense", 0)),
        "speed": _calc_stat(base_stats.get("speed", 45), level, ivs.get("speed", 0)),
    }

    species = get_species(egg.get("species_id", 1))
    sprite = species.sprite if species else "unknown.png"
    name = egg.get("name", "Unknown")

    return {
        "id": egg.get("species_id", 1),
        "name": name,
        "types": egg.get("types", ["normal"]),
        "level": level,
        "stats": stats,
        "current_hp": hp,
        "max_hp": hp,
        "moves": egg.get("moves", [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}]),
        "sprite": sprite,
        "ivs": ivs,
        "gender": egg.get("gender"),
        "is_egg": False,
    }


def collect_egg(game_id: str) -> dict:
    """Collect an egg from the daycare into the player's party."""
    game = get_game(game_id)
    if game is None:
        raise ValueError("Game not found")

    daycare = _get_daycare(game_id)
    if not daycare.egg_ready:
        raise ValueError("No egg available")

    team = game["player"]["team"]
    if len(team) >= 6:
        raise ValueError("Party is full")

    if daycare.slot_1 is None or daycare.slot_2 is None:
        raise ValueError("Need two Pokemon to generate egg")

    egg = generate_egg(daycare.slot_1.pokemon, daycare.slot_2.pokemon)

    # Add egg to party as a dict
    egg_dict = {
        "id": egg.species_id,
        "name": "Egg",
        "types": egg.types,
        "level": 1,
        "stats": {"hp": 10, "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0},
        "current_hp": 10,
        "max_hp": 10,
        "moves": egg.moves,
        "sprite": "egg.png",
        "ivs": egg.ivs,
        "gender": egg.gender,
        "is_egg": True,
        "hatch_counter": egg.hatch_counter,
        "base_stats": egg.base_stats,
    }

    team.append(egg_dict)
    daycare.egg_ready = False
    daycare.egg_steps_accumulated = 0

    return egg_dict
