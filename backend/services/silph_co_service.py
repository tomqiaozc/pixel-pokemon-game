"""Silph Co. event service — Team Rocket takeover."""
from __future__ import annotations
from .item_service import give_item

_state: dict[str, str] = {}

def get_state(game_id: str) -> dict:
    s = _state.get(game_id, "not_entered")
    return {"state": s}

def enter_silph(game_id: str) -> dict:
    s = _state.get(game_id, "not_entered")
    if s != "not_entered":
        return {"error": "already entered"}
    _state[game_id] = "infiltrating"
    return {"state": "infiltrating", "message": "You enter Silph Co. Team Rocket has taken over!"}

def clear_rockets(game_id: str) -> dict:
    s = _state.get(game_id, "not_entered")
    if s != "infiltrating":
        return {"error": "must be infiltrating"}
    _state[game_id] = "rockets_cleared"
    return {"state": "rockets_cleared", "message": "You defeated all the Rocket Grunts on the floors!"}

def defeat_giovanni_silph(game_id: str) -> dict:
    s = _state.get(game_id, "not_entered")
    if s != "rockets_cleared":
        return {"error": "must clear rockets first"}
    _state[game_id] = "president_rescued"
    give_item(game_id, 10)  # Master Ball
    return {"state": "president_rescued", "message": "Giovanni retreats! The President gives you the Master Ball!"}
