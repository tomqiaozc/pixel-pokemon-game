"""Rival trainer API routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.game_service import get_game
from ..services.rival_service import (
    complete_rival_battle,
    get_rival,
    init_rival,
    start_rival_battle,
)

router = APIRouter(prefix="/api/rival", tags=["rival"])


class InitRivalRequest(BaseModel):
    game_id: str
    player_starter_id: int


class RivalBattleRequest(BaseModel):
    game_id: str
    stage: int  # 1=lab, 2=route2, 3=pre-elite


class RivalBattleCompleteRequest(BaseModel):
    game_id: str
    stage: int


@router.post("/init")
def rival_init(req: InitRivalRequest):
    """Initialize the rival based on the player's starter choice."""
    rival = init_rival(req.game_id, req.player_starter_id)
    return rival.model_dump()


@router.get("/{game_id}")
def rival_info(game_id: str):
    """Return current rival data."""
    rival = get_rival(game_id)
    return rival.model_dump()


@router.post("/battle")
def rival_battle(req: RivalBattleRequest):
    """Start a rival battle at the given encounter stage."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    player_team = game["player"]["team"]
    if not player_team:
        raise HTTPException(status_code=400, detail="Player has no Pokemon")

    lead = player_team[0]
    player_pokemon = {
        "species_id": lead["id"],
        "name": lead["name"],
        "types": lead["types"],
        "level": lead["level"],
        "stats": lead["stats"],
        "current_hp": lead.get("current_hp", lead["stats"]["hp"]),
        "max_hp": lead.get("max_hp", lead["stats"]["hp"]),
        "moves": lead["moves"],
        "sprite": lead["sprite"],
        "ability_id": lead.get("ability_id"),
    }

    result = start_rival_battle(req.game_id, req.stage, player_pokemon)
    if result is None:
        raise HTTPException(status_code=400, detail="Could not start rival battle")
    return result.model_dump()


@router.post("/battle-complete")
def rival_battle_complete(req: RivalBattleCompleteRequest):
    """Called when the player wins a rival battle — sets flags and advances quests."""
    complete_rival_battle(req.game_id, req.stage)
    return {"success": True, "message": f"Rival battle stage {req.stage} completed"}
