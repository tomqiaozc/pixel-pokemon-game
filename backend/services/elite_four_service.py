"""Elite Four & Champion battle state machine service."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from .game_service import get_game


class EliteFourState(str, Enum):
    NOT_ENTERED = "not_entered"
    LORELEI = "lorelei"
    LORELEI_DEFEATED = "lorelei_defeated"
    BRUNO = "bruno"
    BRUNO_DEFEATED = "bruno_defeated"
    AGATHA = "agatha"
    AGATHA_DEFEATED = "agatha_defeated"
    LANCE = "lance"
    LANCE_DEFEATED = "lance_defeated"
    CHAMPION = "champion"
    CHAMPION_DEFEATED = "champion_defeated"
    HALL_OF_FAME = "hall_of_fame"


# State progression order
_STATE_ORDER = [
    EliteFourState.NOT_ENTERED,
    EliteFourState.LORELEI,
    EliteFourState.LORELEI_DEFEATED,
    EliteFourState.BRUNO,
    EliteFourState.BRUNO_DEFEATED,
    EliteFourState.AGATHA,
    EliteFourState.AGATHA_DEFEATED,
    EliteFourState.LANCE,
    EliteFourState.LANCE_DEFEATED,
    EliteFourState.CHAMPION,
    EliteFourState.CHAMPION_DEFEATED,
    EliteFourState.HALL_OF_FAME,
]

# Elite Four member data
ELITE_FOUR_MEMBERS = {
    "lorelei": {
        "name": "Lorelei",
        "specialty": "ice",
        "room": "lorelei_room",
        "pokemon_team": [
            {"species_id": 87, "name": "Dewgong", "level": 54, "moves": ["Ice Beam", "Surf", "Aurora Beam", "Rest"]},
            {"species_id": 91, "name": "Cloyster", "level": 53, "moves": ["Spike Cannon", "Clamp", "Aurora Beam", "Supersonic"]},
            {"species_id": 80, "name": "Slowbro", "level": 54, "moves": ["Water Gun", "Psychic", "Amnesia", "Withdraw"]},
            {"species_id": 124, "name": "Jynx", "level": 56, "moves": ["Ice Punch", "Lovely Kiss", "Thrash", "Double Slap"]},
            {"species_id": 131, "name": "Lapras", "level": 56, "moves": ["Body Slam", "Confuse Ray", "Blizzard", "Hydro Pump"]},
        ],
    },
    "bruno": {
        "name": "Bruno",
        "specialty": "fighting",
        "room": "bruno_room",
        "pokemon_team": [
            {"species_id": 95, "name": "Onix", "level": 53, "moves": ["Rock Throw", "Rage", "Slam", "Screech"]},
            {"species_id": 107, "name": "Hitmonchan", "level": 55, "moves": ["Ice Punch", "Fire Punch", "Thunder Punch", "Counter"]},
            {"species_id": 106, "name": "Hitmonlee", "level": 55, "moves": ["Jump Kick", "High Jump Kick", "Mega Kick", "Focus Energy"]},
            {"species_id": 95, "name": "Onix", "level": 56, "moves": ["Rock Throw", "Slam", "Rage", "Harden"]},
            {"species_id": 68, "name": "Machamp", "level": 58, "moves": ["Karate Chop", "Low Kick", "Leer", "Submission"]},
        ],
    },
    "agatha": {
        "name": "Agatha",
        "specialty": "ghost",
        "room": "agatha_room",
        "pokemon_team": [
            {"species_id": 94, "name": "Gengar", "level": 56, "moves": ["Confuse Ray", "Night Shade", "Hypnosis", "Dream Eater"]},
            {"species_id": 42, "name": "Golbat", "level": 56, "moves": ["Wing Attack", "Confuse Ray", "Bite", "Screech"]},
            {"species_id": 93, "name": "Haunter", "level": 55, "moves": ["Confuse Ray", "Night Shade", "Hypnosis", "Dream Eater"]},
            {"species_id": 24, "name": "Arbok", "level": 58, "moves": ["Bite", "Glare", "Screech", "Acid"]},
            {"species_id": 94, "name": "Gengar", "level": 60, "moves": ["Confuse Ray", "Night Shade", "Toxic", "Dream Eater"]},
        ],
    },
    "lance": {
        "name": "Lance",
        "specialty": "dragon",
        "room": "lance_room",
        "pokemon_team": [
            {"species_id": 130, "name": "Gyarados", "level": 58, "moves": ["Dragon Rage", "Hydro Pump", "Hyper Beam", "Leer"]},
            {"species_id": 148, "name": "Dragonair", "level": 56, "moves": ["Thunder Wave", "Slam", "Agility", "Hyper Beam"]},
            {"species_id": 148, "name": "Dragonair", "level": 56, "moves": ["Thunder Wave", "Slam", "Dragon Rage", "Hyper Beam"]},
            {"species_id": 142, "name": "Aerodactyl", "level": 60, "moves": ["Wing Attack", "Hyper Beam", "Bite", "Supersonic"]},
            {"species_id": 149, "name": "Dragonite", "level": 62, "moves": ["Blizzard", "Thunder", "Hyper Beam", "Fire Blast"]},
        ],
    },
}

CHAMPION_DATA = {
    "name": "Champion",
    "room": "champion_room",
    "pokemon_team": [
        {"species_id": 18, "name": "Pidgeot", "level": 61, "moves": ["Wing Attack", "Mirror Move", "Sky Attack", "Whirlwind"]},
        {"species_id": 65, "name": "Alakazam", "level": 59, "moves": ["Psychic", "Recover", "Kinesis", "Reflect"]},
        {"species_id": 112, "name": "Rhydon", "level": 61, "moves": ["Earthquake", "Horn Drill", "Leer", "Tail Whip"]},
        {"species_id": 59, "name": "Arcanine", "level": 63, "moves": ["Flamethrower", "Fire Blast", "Extreme Speed", "Roar"]},
        {"species_id": 130, "name": "Gyarados", "level": 63, "moves": ["Hydro Pump", "Dragon Rage", "Hyper Beam", "Leer"]},
        {"species_id": 3, "name": "Venusaur", "level": 65, "moves": ["Solar Beam", "Mega Drain", "Razor Leaf", "Sleep Powder"]},
    ],
}

# In-memory state per game
_elite_four_state: dict[str, EliteFourState] = {}
_hall_of_fame: dict[str, list[dict]] = {}


def get_elite_four_state(game_id: str) -> dict:
    """Get current Elite Four progression state."""
    state = _elite_four_state.get(game_id, EliteFourState.NOT_ENTERED)
    return {
        "game_id": game_id,
        "state": state.value,
        "next_battle": _get_next_battle(state),
        "defeated": _get_defeated_members(state),
    }


def _get_next_battle(state: EliteFourState) -> Optional[str]:
    """Get the next battle based on current state."""
    mapping = {
        EliteFourState.NOT_ENTERED: "lorelei",
        EliteFourState.LORELEI_DEFEATED: "bruno",
        EliteFourState.BRUNO_DEFEATED: "agatha",
        EliteFourState.AGATHA_DEFEATED: "lance",
        EliteFourState.LANCE_DEFEATED: "champion",
    }
    return mapping.get(state)


def _get_defeated_members(state: EliteFourState) -> list[str]:
    """Get list of defeated Elite Four members."""
    defeated = []
    order = ["lorelei", "bruno", "agatha", "lance", "champion"]
    state_idx = _STATE_ORDER.index(state) if state in _STATE_ORDER else 0
    for i, member in enumerate(order):
        # Each member is defeated at index 2 + (i * 2) in _STATE_ORDER
        defeated_idx = 2 + (i * 2)
        if state_idx >= defeated_idx:
            defeated.append(member)
    return defeated


def enter_elite_four(game_id: str) -> dict:
    """Enter the Elite Four challenge. Requires all 8 badges."""
    game = get_game(game_id)
    if game is None:
        return {"error": "Game not found"}
    _elite_four_state[game_id] = EliteFourState.LORELEI
    return get_elite_four_state(game_id)


def get_member_data(member_id: str) -> Optional[dict]:
    """Get Elite Four member or Champion data."""
    if member_id == "champion":
        return CHAMPION_DATA
    return ELITE_FOUR_MEMBERS.get(member_id)


def defeat_member(game_id: str, member_id: str) -> dict:
    """Record defeating an Elite Four member or Champion."""
    state = _elite_four_state.get(game_id, EliteFourState.NOT_ENTERED)

    transitions = {
        ("lorelei", EliteFourState.LORELEI): EliteFourState.LORELEI_DEFEATED,
        ("bruno", EliteFourState.BRUNO): EliteFourState.BRUNO_DEFEATED,
        ("agatha", EliteFourState.AGATHA): EliteFourState.AGATHA_DEFEATED,
        ("lance", EliteFourState.LANCE): EliteFourState.LANCE_DEFEATED,
        ("champion", EliteFourState.CHAMPION): EliteFourState.CHAMPION_DEFEATED,
    }

    new_state = transitions.get((member_id, state))
    if new_state is None:
        return {"error": f"Cannot defeat {member_id} in current state {state.value}"}

    _elite_four_state[game_id] = new_state

    # Auto-advance to next battle
    advance = {
        EliteFourState.LORELEI_DEFEATED: EliteFourState.BRUNO,
        EliteFourState.BRUNO_DEFEATED: EliteFourState.AGATHA,
        EliteFourState.AGATHA_DEFEATED: EliteFourState.LANCE,
        EliteFourState.LANCE_DEFEATED: EliteFourState.CHAMPION,
        EliteFourState.CHAMPION_DEFEATED: EliteFourState.HALL_OF_FAME,
    }
    if new_state in advance:
        _elite_four_state[game_id] = advance[new_state]

    return get_elite_four_state(game_id)


def enter_hall_of_fame(game_id: str) -> dict:
    """Enter the Hall of Fame after defeating the Champion."""
    state = _elite_four_state.get(game_id, EliteFourState.NOT_ENTERED)
    if state != EliteFourState.HALL_OF_FAME:
        return {"error": "Must defeat the Champion first"}

    game = get_game(game_id)
    entry = {
        "game_id": game_id,
        "message": "Congratulations! You are the new Pokemon League Champion!",
    }

    if game_id not in _hall_of_fame:
        _hall_of_fame[game_id] = []
    _hall_of_fame[game_id].append(entry)

    return entry


def get_hall_of_fame(game_id: str) -> list[dict]:
    """Get Hall of Fame entries for a game."""
    return _hall_of_fame.get(game_id, [])


def reset_elite_four(game_id: str) -> dict:
    """Reset Elite Four progress (e.g., after losing)."""
    _elite_four_state[game_id] = EliteFourState.NOT_ENTERED
    return get_elite_four_state(game_id)
