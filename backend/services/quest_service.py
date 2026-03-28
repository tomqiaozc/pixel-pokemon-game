"""Quest system, story flags, and progression service."""
from __future__ import annotations

from copy import deepcopy
from typing import Optional

from ..models.quest import (
    Quest,
    QuestCheckResult,
    QuestCompleteResult,
    QuestObjective,
    QuestReward,
    StoryFlags,
)
from .game_service import get_game

# In-memory stores (per game_id)
_player_quests: dict[str, list[Quest]] = {}
_story_flags: dict[str, dict[str, bool]] = {}

# --- Seed quest definitions ---
_QUEST_DEFS: list[dict] = [
    {
        "id": "new_adventure",
        "name": "A New Adventure",
        "description": "Choose your starter Pokemon and begin your journey!",
        "type": "main",
        "objectives": [
            {"id": "choose_starter", "description": "Choose a starter Pokemon", "type": "collect_item", "target": "starter", "required_progress": 1},
        ],
        "rewards": {"money": 500, "items": [{"item_id": 7, "quantity": 5}], "unlock_flags": ["has_starter"]},
        "prerequisite_quests": [],
        "status": "active",
    },
    {
        "id": "oaks_parcel",
        "name": "Oak's Parcel",
        "description": "Buy a parcel at Viridian Mart and deliver it to Professor Oak.",
        "type": "main",
        "objectives": [
            {"id": "visit_viridian", "description": "Visit Viridian City", "type": "visit_location", "target": "viridian_city", "required_progress": 1},
            {"id": "deliver_parcel", "description": "Deliver the parcel to Professor Oak", "type": "deliver_item", "target": "oaks_lab", "required_progress": 1},
        ],
        "rewards": {"money": 1000, "unlock_flags": ["has_pokedex", "oak_parcel_delivered"]},
        "prerequisite_quests": ["new_adventure"],
    },
    {
        "id": "boulder_badge",
        "name": "The Boulder Badge",
        "description": "Defeat Brock at Pewter City Gym to earn the Boulder Badge.",
        "type": "main",
        "objectives": [
            {"id": "defeat_brock", "description": "Defeat Gym Leader Brock", "type": "defeat_gym", "target": "pewter_gym", "required_progress": 1},
        ],
        "rewards": {"money": 2000, "unlock_flags": ["badge_boulder"]},
        "prerequisite_quests": ["oaks_parcel"],
    },
    {
        "id": "cascade_badge",
        "name": "The Cascade Badge",
        "description": "Defeat Misty at Cerulean City Gym to earn the Cascade Badge.",
        "type": "main",
        "objectives": [
            {"id": "defeat_misty", "description": "Defeat Gym Leader Misty", "type": "defeat_gym", "target": "cerulean_gym", "required_progress": 1},
        ],
        "rewards": {"money": 3000, "unlock_flags": ["badge_cascade"]},
        "prerequisite_quests": ["boulder_badge"],
    },
    {
        "id": "rival_showdown_1",
        "name": "Rival Showdown I",
        "description": "Your rival is waiting on Route 2. Defeat them to prove your strength!",
        "type": "main",
        "objectives": [
            {"id": "defeat_rival_route2", "description": "Defeat your rival on Route 2", "type": "defeat_trainer", "target": "rival_route2", "required_progress": 1},
        ],
        "rewards": {"money": 1500, "unlock_flags": ["rival_defeated_route2"]},
        "prerequisite_quests": ["oaks_parcel"],
    },
]


def _init_quests(game_id: str) -> list[Quest]:
    """Initialize quest list for a new player."""
    quests = []
    for qdef in _QUEST_DEFS:
        q = Quest(
            id=qdef["id"],
            name=qdef["name"],
            description=qdef["description"],
            type=qdef.get("type", "main"),
            objectives=[QuestObjective(**o) for o in qdef["objectives"]],
            rewards=QuestReward(**qdef.get("rewards", {})),
            prerequisite_quests=qdef.get("prerequisite_quests", []),
            status=qdef.get("status", "locked"),
        )
        quests.append(q)
    _player_quests[game_id] = quests
    return quests


def _get_quests(game_id: str) -> list[Quest]:
    if game_id not in _player_quests:
        return _init_quests(game_id)
    return _player_quests[game_id]


def _get_flags(game_id: str) -> dict[str, bool]:
    if game_id not in _story_flags:
        _story_flags[game_id] = {}
    return _story_flags[game_id]


# --- Story flags ---

def get_story_flags(game_id: str) -> dict[str, bool]:
    return _get_flags(game_id)


def get_story_flag(game_id: str, flag_name: str) -> bool:
    return _get_flags(game_id).get(flag_name, False)


def set_story_flag(game_id: str, flag_name: str, value: bool = True) -> dict[str, bool]:
    flags = _get_flags(game_id)
    flags[flag_name] = value
    return flags


# --- Quest operations ---

def get_all_quests(game_id: str) -> list[Quest]:
    """Return all quests with current status for the player."""
    game = get_game(game_id)
    if game is None:
        return []
    quests = _get_quests(game_id)
    _refresh_quest_status(game_id, quests)
    return quests


def get_quest(game_id: str, quest_id: str) -> Optional[Quest]:
    quests = _get_quests(game_id)
    for q in quests:
        if q.id == quest_id:
            return q
    return None


def _refresh_quest_status(game_id: str, quests: list[Quest]) -> None:
    """Unlock quests whose prerequisites are all completed."""
    completed_ids = {q.id for q in quests if q.status == "completed"}
    for q in quests:
        if q.status == "locked":
            if all(pid in completed_ids for pid in q.prerequisite_quests):
                q.status = "active"


def check_quest_progress(game_id: str, event_type: str, event_data: dict) -> QuestCheckResult:
    """Check if any active quest objectives were advanced by this event."""
    game = get_game(game_id)
    if game is None:
        return QuestCheckResult()

    quests = _get_quests(game_id)
    _refresh_quest_status(game_id, quests)

    updated: list[Quest] = []
    completed: list[Quest] = []
    newly_active: list[Quest] = []

    for quest in quests:
        if quest.status != "active":
            continue

        quest_updated = False
        for obj in quest.objectives:
            if obj.type == event_type and obj.current_progress < obj.required_progress:
                # Match target
                target_key = _get_target_key(event_type)
                if target_key and event_data.get(target_key) == obj.target:
                    obj.current_progress = min(obj.current_progress + 1, obj.required_progress)
                    quest_updated = True

        if quest_updated:
            updated.append(quest)
            # Check if all objectives complete
            if all(o.current_progress >= o.required_progress for o in quest.objectives):
                _complete_quest(game_id, quest)
                completed.append(quest)

    # Check for newly unlocked quests
    if completed:
        _refresh_quest_status(game_id, quests)
        for q in quests:
            if q.status == "active" and q not in updated:
                newly_active.append(q)

    return QuestCheckResult(
        updated_quests=updated,
        completed_quests=completed,
        newly_active_quests=newly_active,
    )


def _get_target_key(event_type: str) -> Optional[str]:
    """Map event type to the key in event_data that contains the target."""
    mapping = {
        "defeat_trainer": "trainer_id",
        "visit_location": "map_id",
        "collect_item": "item_id",
        "deliver_item": "location_id",
        "catch_pokemon": "species_id",
        "defeat_gym": "gym_id",
    }
    return mapping.get(event_type)


def _complete_quest(game_id: str, quest: Quest) -> None:
    """Mark quest as completed and apply rewards."""
    quest.status = "completed"

    # Set story flags from rewards
    for flag in quest.rewards.unlock_flags:
        set_story_flag(game_id, flag)

    # Apply money reward
    if quest.rewards.money > 0:
        game = get_game(game_id)
        if game:
            money = game["player"].get("money", 0)
            game["player"]["money"] = money + quest.rewards.money

    # Apply item rewards
    if quest.rewards.items:
        game = get_game(game_id)
        if game:
            inventory = game["player"].setdefault("inventory", [])
            for item_reward in quest.rewards.items:
                found = False
                for entry in inventory:
                    if entry.get("item_id") == item_reward["item_id"]:
                        entry["quantity"] += item_reward["quantity"]
                        found = True
                        break
                if not found:
                    inventory.append({"item_id": item_reward["item_id"], "quantity": item_reward["quantity"]})


def complete_quest_manual(game_id: str, quest_id: str) -> Optional[QuestCompleteResult]:
    """Manually mark a quest as complete (for scripted events)."""
    game = get_game(game_id)
    if game is None:
        return None

    quest = get_quest(game_id, quest_id)
    if quest is None or quest.status == "completed":
        return None

    # Force all objectives to complete
    for obj in quest.objectives:
        obj.current_progress = obj.required_progress

    _complete_quest(game_id, quest)

    # Find newly unlocked quests
    quests = _get_quests(game_id)
    _refresh_quest_status(game_id, quests)
    newly_unlocked = [q.id for q in quests if q.status == "active" and q.id != quest_id]

    return QuestCompleteResult(
        quest=quest,
        rewards_given=quest.rewards,
        newly_unlocked_quests=newly_unlocked,
    )


# --- Area gating ---

def check_area_accessible(game_id: str, map_id: str, required_flag: Optional[str] = None) -> dict:
    """Check if a player can enter a map based on story flags."""
    if required_flag is None:
        return {"accessible": True, "reason": None}

    has_flag = get_story_flag(game_id, required_flag)
    if has_flag:
        return {"accessible": True, "reason": None}

    # Generate human-readable reason
    flag_reasons = {
        "has_starter": "You need to choose a starter Pokemon first",
        "has_pokedex": "You need to get the Pokedex from Professor Oak",
        "oak_parcel_delivered": "You need to deliver Oak's Parcel first",
        "badge_boulder": "You need the Boulder Badge to pass",
        "badge_cascade": "You need the Cascade Badge to pass",
        "rival_defeated_route2": "You need to defeat your rival on Route 2 first",
    }
    reason = flag_reasons.get(required_flag, f"You need to complete a requirement: {required_flag}")
    return {"accessible": False, "reason": reason}
