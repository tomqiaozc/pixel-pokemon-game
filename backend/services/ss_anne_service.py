"""S.S. Anne event service — ticket gate, rival battle, captain event, ship departure."""

from __future__ import annotations

from .item_service import give_item

# In-memory state: game_id -> S.S. Anne event progress
_ss_anne_state: dict[str, dict] = {}


def get_state(game_id: str) -> dict:
    """Return S.S. Anne event state."""
    if game_id not in _ss_anne_state:
        _ss_anne_state[game_id] = {
            "boarded": False,
            "rival_defeated": False,
            "captain_helped": False,
            "hm_received": False,
            "ship_departed": False,
        }
    return _ss_anne_state[game_id]


def board_ship(game_id: str, has_ticket: bool) -> dict:
    """Player attempts to board the S.S. Anne."""
    if not has_ticket:
        return {"success": False, "error": "No S.S. Ticket"}
    state = get_state(game_id)
    state["boarded"] = True
    return {"success": True}


def defeat_rival(game_id: str) -> dict:
    """Record rival defeat aboard the S.S. Anne."""
    state = get_state(game_id)
    if not state["boarded"]:
        return {"success": False, "error": "Not on ship"}
    state["rival_defeated"] = True
    return {"success": True}


def help_captain(game_id: str) -> dict:
    """Player helps the seasick captain."""
    state = get_state(game_id)
    if not state["boarded"]:
        return {"success": False, "error": "Not on ship"}
    state["captain_helped"] = True
    return {"success": True}


def receive_hm(game_id: str) -> dict:
    """Captain gives HM01 Cut after being helped."""
    state = get_state(game_id)
    if not state["captain_helped"]:
        return {"success": False, "error": "Captain not helped yet"}
    if state["hm_received"]:
        return {"success": True, "already_received": True}
    give_item(game_id, 53, 1)  # HM01 Cut
    state["hm_received"] = True
    state["ship_departed"] = True
    return {"success": True, "item": "HM01 Cut"}
