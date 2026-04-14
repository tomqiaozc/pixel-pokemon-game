"""Silph Co. API endpoints."""
from __future__ import annotations
from fastapi import APIRouter
from ..services.silph_co_service import (
    get_state, enter_silph, clear_rockets, defeat_giovanni_silph
)

router = APIRouter(prefix="/api/silph-co", tags=["silph-co"])

@router.get("/state")
def silph_co_state(game_id: str = "default"):
    return get_state(game_id)

@router.post("/enter")
def silph_co_enter(game_id: str = "default"):
    return enter_silph(game_id)

@router.post("/clear-rockets")
def silph_co_clear_rockets(game_id: str = "default"):
    return clear_rockets(game_id)

@router.post("/defeat-giovanni")
def silph_co_defeat_giovanni(game_id: str = "default"):
    return defeat_giovanni_silph(game_id)
