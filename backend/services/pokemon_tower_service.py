"""Pokemon Tower event service — ghost encounters, Silph Scope, Mr. Fuji rescue."""
from __future__ import annotations

from .item_service import give_item

_tower_state: dict[str, dict] = {}

TOWER_FLOORS = 4  # 1F, 2F, 3F, Top


def get_state(game_id: str) -> dict:
    if game_id not in _tower_state:
        _tower_state[game_id] = {
            "entered": False,
            "current_floor": 0,
            "ghost_blocked": False,
            "has_scope": False,
            "ghost_revealed": False,
            "rockets_defeated": False,
            "fuji_rescued": False,
            "floors_cleared": [],
        }
    return _tower_state[game_id]


def enter_tower(game_id: str) -> dict:
    state = get_state(game_id)
    state["entered"] = True
    state["current_floor"] = 1
    return {"success": True}


def encounter_ghost(game_id: str, floor: int) -> dict:
    state = get_state(game_id)
    if not state["entered"]:
        return {"success": False, "error": "Not in tower"}
    if floor >= 3 and not state["has_scope"]:
        state["ghost_blocked"] = True
        return {"success": False, "blocked": True, "message": "A ghost blocks your way! You can't identify it!"}
    state["current_floor"] = floor
    if floor not in state["floors_cleared"]:
        state["floors_cleared"].append(floor)
    return {"success": True, "floor": floor}


def use_silph_scope(game_id: str) -> dict:
    state = get_state(game_id)
    if not state["ghost_blocked"]:
        return {"success": False, "error": "No ghost to reveal"}
    state["has_scope"] = True
    state["ghost_revealed"] = True
    state["ghost_blocked"] = False
    return {"success": True, "message": "The ghost is revealed to be a Marowak!"}


def defeat_rockets(game_id: str) -> dict:
    state = get_state(game_id)
    if not state["entered"]:
        return {"success": False, "error": "Not in tower"}
    state["rockets_defeated"] = True
    return {"success": True}


def rescue_fuji(game_id: str) -> dict:
    state = get_state(game_id)
    if not state["rockets_defeated"]:
        return {"success": False, "error": "Rockets still present"}
    if state["fuji_rescued"]:
        return {"success": True, "already_rescued": True}
    state["fuji_rescued"] = True
    give_item(game_id, 55, 1)  # Poke Flute
    return {"success": True, "item": "Poke Flute"}
