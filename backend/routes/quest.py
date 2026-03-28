"""Quest and story flag API routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.quest import QuestCheckRequest
from ..services.quest_service import (
    check_area_accessible,
    check_quest_progress,
    complete_quest_manual,
    get_all_quests,
    get_quest,
    get_story_flag,
    get_story_flags,
    set_story_flag,
)

router = APIRouter(tags=["quests"])


# --- Request models ---

class SetFlagRequest(BaseModel):
    game_id: str
    flag_name: str
    value: bool = True


class AreaAccessRequest(BaseModel):
    game_id: str
    map_id: str
    required_flag: Optional[str] = None


# --- Quest endpoints ---

@router.get("/api/quests/{game_id}")
def list_quests(game_id: str):
    """Return all quests with current status for the player."""
    quests = get_all_quests(game_id)
    if not quests:
        raise HTTPException(status_code=404, detail="Game not found or no quests")
    return [q.model_dump() for q in quests]


@router.get("/api/quests/{game_id}/{quest_id}")
def quest_detail(game_id: str, quest_id: str):
    """Return a single quest by ID."""
    quest = get_quest(game_id, quest_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    return quest.model_dump()


@router.post("/api/quests/check-progress")
def check_progress(req: QuestCheckRequest):
    """Check if an event advances any active quest objectives."""
    result = check_quest_progress(req.game_id, req.event_type, req.event_data)
    return result.model_dump()


@router.post("/api/quests/{game_id}/{quest_id}/complete")
def complete_quest(game_id: str, quest_id: str):
    """Manually complete a quest (for scripted events)."""
    result = complete_quest_manual(game_id, quest_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Quest not found or already completed")
    return result.model_dump()


# --- Story flag endpoints (separate prefix to avoid collision with quest routes) ---

@router.get("/api/flags/{game_id}")
def list_flags(game_id: str):
    """Return all story flags for a game."""
    return get_story_flags(game_id)


@router.get("/api/flags/{game_id}/{flag_name}")
def get_flag(game_id: str, flag_name: str):
    """Return the value of a single story flag."""
    return {"flag_name": flag_name, "value": get_story_flag(game_id, flag_name)}


@router.post("/api/flags/set")
def set_flag(req: SetFlagRequest):
    """Set a story flag value."""
    flags = set_story_flag(req.game_id, req.flag_name, req.value)
    return flags


# --- Area gating ---

@router.post("/api/quests/area-check")
def area_accessible(req: AreaAccessRequest):
    """Check if a player can enter a map based on story flags."""
    return check_area_accessible(req.game_id, req.map_id, req.required_flag)
