"""Lt. Surge's Gym trash can puzzle — find 2 switches to unlock the path."""

from __future__ import annotations

import random

# In-memory state: game_id -> puzzle progress
_puzzle_state: dict[str, dict] = {}

TRASH_CAN_COUNT = 15


def _init_puzzle(game_id: str) -> dict:
    """Randomly place 2 switches in 15 trash cans."""
    switches = random.sample(range(TRASH_CAN_COUNT), 2)
    _puzzle_state[game_id] = {
        "switch_positions": switches,
        "first_found": False,
        "first_can": None,
        "solved": False,
        "checked_cans": [],
    }
    return _puzzle_state[game_id]


def get_state(game_id: str) -> dict:
    """Return current puzzle state (public view)."""
    if game_id not in _puzzle_state:
        _init_puzzle(game_id)
    state = _puzzle_state[game_id]
    return {
        "first_found": state["first_found"],
        "solved": state["solved"],
        "checked_cans": state["checked_cans"],
    }


def check_can(game_id: str, can_index: int) -> dict:
    """Player checks a trash can for a switch."""
    if game_id not in _puzzle_state:
        _init_puzzle(game_id)
    state = _puzzle_state[game_id]

    if state["solved"]:
        return {"result": "already_solved", "solved": True}

    if can_index not in state["checked_cans"]:
        state["checked_cans"].append(can_index)

    is_switch = can_index in state["switch_positions"]

    if not is_switch:
        if state["first_found"]:
            # Wrong second switch — reset
            state["first_found"] = False
            state["first_can"] = None
            state["checked_cans"] = []
            return {"result": "wrong_reset", "message": "Nope! The switches reset!", "solved": False}
        return {"result": "empty", "message": "There's nothing in this trash can.", "solved": False}

    if not state["first_found"]:
        state["first_found"] = True
        state["first_can"] = can_index
        return {"result": "first_switch", "message": "Hey! There's a switch in this trash can!", "solved": False}
    else:
        state["solved"] = True
        return {"result": "second_switch", "message": "The second switch! The electric barrier is down!", "solved": True}


def reset_puzzle(game_id: str) -> dict:
    """Reset the puzzle with new switch positions."""
    _init_puzzle(game_id)
    return get_state(game_id)
