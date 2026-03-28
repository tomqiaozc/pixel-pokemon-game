"""Held item and evolution stone API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.held_item_service import (
    equip_held_item,
    execute_stone_evolution,
    get_all_held_items,
    get_evolution_stones,
    remove_held_item,
)
from ..services.game_service import get_game

router = APIRouter(prefix="/api", tags=["held-items"])


class HoldItemRequest(BaseModel):
    game_id: str
    pokemon_index: int
    item_id: str


class RemoveItemRequest(BaseModel):
    game_id: str
    pokemon_index: int


class StoneEvolutionRequest(BaseModel):
    game_id: str
    pokemon_index: int
    stone_id: str


@router.get("/items/held-effects")
def list_held_effects():
    """List all held item effect definitions for UI tooltips."""
    return get_all_held_items()


@router.post("/pokemon/hold-item")
def hold_item(req: HoldItemRequest):
    """Equip a held item on a Pokemon."""
    try:
        result = equip_held_item(req.game_id, req.pokemon_index, req.item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.post("/pokemon/remove-item")
def remove_item(req: RemoveItemRequest):
    """Remove held item from a Pokemon."""
    try:
        result = remove_held_item(req.game_id, req.pokemon_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.post("/evolution/stone")
def use_stone(req: StoneEvolutionRequest):
    """Use an evolution stone on a Pokemon."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    team = game["player"]["team"]
    if req.pokemon_index < 0 or req.pokemon_index >= len(team):
        raise HTTPException(status_code=400, detail="Invalid Pokemon index")

    pokemon = team[req.pokemon_index]
    result = execute_stone_evolution(pokemon, req.stone_id)
    if result is None:
        raise HTTPException(status_code=400, detail="This Pokemon cannot evolve with that stone")
    return result
