"""Bill's House transformation event service."""

from __future__ import annotations

from ..services.item_service import give_item

# In-memory state: game_id -> bill event progress
_bill_state: dict[str, dict] = {}

VALID_STATES = ["pokemon", "transforming", "human", "ticket_given"]


def get_state(game_id: str) -> dict:
    """Return Bill's current event state."""
    if game_id not in _bill_state:
        _bill_state[game_id] = {"state": "pokemon"}
    return _bill_state[game_id]


def start_transformation(game_id: str) -> dict:
    """Player activates the Cell Separation System."""
    state = get_state(game_id)
    if state["state"] in ("human", "ticket_given"):
        return {"success": True, "state": state["state"], "already_complete": True}
    if state["state"] == "transforming":
        return {"success": True, "state": state["state"], "already_started": True}
    if state["state"] != "pokemon":
        return {"success": False, "error": "Bill is not in Pokemon form"}
    state["state"] = "transforming"
    return {"success": True, "state": state["state"]}


def complete_transformation(game_id: str) -> dict:
    """Bill transforms back to human form."""
    state = get_state(game_id)
    if state["state"] in ("human", "ticket_given"):
        return {"success": True, "state": state["state"], "already_complete": True}
    if state["state"] != "transforming":
        return {"success": False, "error": "Transformation not started"}
    state["state"] = "human"
    return {"success": True, "state": state["state"]}


def give_ss_ticket(game_id: str) -> dict:
    """Bill gives S.S. Ticket after being rescued."""
    state = get_state(game_id)
    if state["state"] == "ticket_given":
        return {"success": True, "already_given": True}
    if state["state"] != "human":
        return {"success": False, "error": "Bill hasn't been rescued yet"}
    give_item(game_id, 52, 1)
    state["state"] = "ticket_given"
    return {"success": True, "item": "S.S. Ticket", "state": "ticket_given"}
