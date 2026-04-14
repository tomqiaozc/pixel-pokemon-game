"""Nugget Bridge gauntlet service — tracks sequential trainer defeats and Nugget reward."""

from __future__ import annotations

from ..services.item_service import give_item

# In-memory state: game_id -> bridge progress
_nugget_bridge_state: dict[str, dict] = {}

BRIDGE_TRAINER_COUNT = 5


def _raw_state(game_id: str) -> dict:
    """Return raw internal state dict."""
    if game_id not in _nugget_bridge_state:
        _nugget_bridge_state[game_id] = {
            "trainers_defeated": [],
            "nugget_awarded": False,
            "rocket_defeated": False,
        }
    return _nugget_bridge_state[game_id]


def get_state(game_id: str) -> dict:
    """Return current Nugget Bridge progress (public view)."""
    raw = _raw_state(game_id)
    return {
        "trainers_defeated": len(raw["trainers_defeated"]),
        "trainers_defeated_list": raw["trainers_defeated"],
        "nugget_awarded": raw["nugget_awarded"],
        "rocket_defeated": raw["rocket_defeated"],
        "bridge_clear": all(i in raw["trainers_defeated"] for i in range(BRIDGE_TRAINER_COUNT)),
    }


def defeat_trainer(game_id: str, trainer_index: int) -> dict:
    """Record a trainer defeat on the bridge (indices 0-4)."""
    raw = _raw_state(game_id)
    if 0 <= trainer_index < BRIDGE_TRAINER_COUNT and trainer_index not in raw["trainers_defeated"]:
        raw["trainers_defeated"].append(trainer_index)
        raw["trainers_defeated"].sort()
    return get_state(game_id)


def is_bridge_clear(game_id: str) -> bool:
    """Check if all 5 bridge trainers are defeated."""
    raw = _raw_state(game_id)
    return all(i in raw["trainers_defeated"] for i in range(BRIDGE_TRAINER_COUNT))


def award_nugget(game_id: str) -> dict:
    """Award the Nugget after clearing all 5 trainers."""
    raw = _raw_state(game_id)
    if not is_bridge_clear(game_id):
        return {"success": False, "error": "Not all trainers defeated"}
    if raw["nugget_awarded"]:
        return {"success": False, "error": "Nugget already awarded"}
    give_item(game_id, 51, 1)
    raw["nugget_awarded"] = True
    return {"success": True, "item": "Nugget"}


def defeat_rocket(game_id: str) -> dict:
    """Record Rocket Grunt defeat at end of bridge."""
    raw = _raw_state(game_id)
    raw["rocket_defeated"] = True
    return get_state(game_id)
