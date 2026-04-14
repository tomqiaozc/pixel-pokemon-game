"""Rocket Hideout event service — Game Corner basement."""
from __future__ import annotations
from .item_service import give_item

_state: dict[str, str] = {}

def get_state(game_id: str) -> dict:
    s = _state.get(game_id, "not_entered")
    return {"state": s}

def enter_hideout(game_id: str) -> dict:
    s = _state.get(game_id, "not_entered")
    if s != "not_entered":
        return {"error": "already entered"}
    _state[game_id] = "b1f_entered"
    return {"state": "b1f_entered", "message": "You found a secret staircase behind the poster!"}

def clear_floor(game_id: str, floor: str) -> dict:
    s = _state.get(game_id, "not_entered")
    transitions = {
        "b2f": ("b1f_entered", "b2f_cleared"),
        "b3f": ("b2f_cleared", "b3f_cleared"),
    }
    if floor not in transitions:
        return {"error": "invalid floor"}
    required, next_state = transitions[floor]
    if s != required:
        return {"error": f"must be in {required} state"}
    _state[game_id] = next_state
    return {"state": next_state, "message": f"Floor {floor} cleared!"}

def defeat_giovanni(game_id: str) -> dict:
    s = _state.get(game_id, "not_entered")
    if s != "b3f_cleared":
        return {"error": "must clear B3F first"}
    _state[game_id] = "giovanni_defeated"
    give_item(game_id, 54)  # Silph Scope
    return {"state": "giovanni_defeated", "message": "Giovanni defeated! You received the Silph Scope!"}
