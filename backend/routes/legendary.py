"""Legendary Pokemon API routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..services.legendary_service import (
    check_legendary,
    get_all_legendaries,
    mark_legendary_caught,
    mark_legendary_fainted,
    mark_legendary_fled,
    start_legendary_encounter,
)

router = APIRouter(prefix="/api/legendary", tags=["legendary"])


@router.get("/{game_id}")
def list_legendaries(game_id: str):
    """Return all legendaries with availability status for the player."""
    entries = get_all_legendaries(game_id)
    return [e.model_dump() for e in entries]


@router.get("/{game_id}/{species_id}/check")
def legendary_check(game_id: str, species_id: int):
    """Check if a legendary is available for encounter."""
    result = check_legendary(game_id, species_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Legendary not found")
    return result.model_dump()


@router.post("/{game_id}/{species_id}/encounter")
def legendary_encounter(game_id: str, species_id: int):
    """Start a legendary battle. Validates requirements and one-time status."""
    result = start_legendary_encounter(game_id, species_id)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot encounter this legendary — requirements not met, already caught, or fainted",
        )
    return result.model_dump()


@router.post("/{game_id}/{species_id}/caught")
def legendary_caught(game_id: str, species_id: int):
    """Mark a legendary as caught after successful catch."""
    mark_legendary_caught(game_id, species_id)
    return {"success": True, "message": "Legendary marked as caught"}


@router.post("/{game_id}/{species_id}/fainted")
def legendary_fainted(game_id: str, species_id: int):
    """Mark a legendary as fainted — permanently unavailable."""
    mark_legendary_fainted(game_id, species_id)
    return {"success": True, "message": "Legendary marked as fainted"}


@router.post("/{game_id}/{species_id}/fled")
def legendary_fled(game_id: str, species_id: int):
    """Player ran or whited out — legendary returns to available."""
    mark_legendary_fled(game_id, species_id)
    return {"success": True, "message": "Legendary returned to available"}
