"""Rocket Hideout API endpoints."""
from __future__ import annotations
from fastapi import APIRouter
from ..services.rocket_hideout_service import (
    get_state, enter_hideout, clear_floor, defeat_giovanni
)

router = APIRouter(prefix="/api/rocket-hideout", tags=["rocket-hideout"])

@router.get("/state")
def rocket_hideout_state(game_id: str = "default"):
    return get_state(game_id)

@router.post("/enter")
def rocket_hideout_enter(game_id: str = "default"):
    return enter_hideout(game_id)

@router.post("/clear-floor")
def rocket_hideout_clear_floor(game_id: str = "default", floor: str = "b2f"):
    return clear_floor(game_id, floor)

@router.post("/defeat-giovanni")
def rocket_hideout_defeat_giovanni(game_id: str = "default"):
    return defeat_giovanni(game_id)
