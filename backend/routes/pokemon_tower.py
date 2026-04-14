from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.game_service import get_game
from ..services.pokemon_tower_service import (
    get_state, enter_tower, encounter_ghost,
    use_silph_scope, defeat_rockets, rescue_fuji,
)

router = APIRouter(prefix="/api/pokemon-tower", tags=["pokemon-tower"])


class TowerRequest(BaseModel):
    game_id: str


class GhostRequest(BaseModel):
    game_id: str
    floor: int


@router.get("/state/{game_id}")
def tower_state(game_id: str):
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_state(game_id)


@router.post("/enter")
def enter(req: TowerRequest):
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return enter_tower(req.game_id)


@router.post("/ghost")
def ghost(req: GhostRequest):
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = encounter_ghost(req.game_id, req.floor)
    if not result.get("success") and not result.get("blocked"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/scope")
def scope(req: TowerRequest):
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = use_silph_scope(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/rockets")
def rockets(req: TowerRequest):
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return defeat_rockets(req.game_id)


@router.post("/rescue")
def rescue(req: TowerRequest):
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = rescue_fuji(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
