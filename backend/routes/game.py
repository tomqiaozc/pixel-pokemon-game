from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.game_service import create_game, get_game, save_game

router = APIRouter(prefix="/api/game", tags=["game"])


class NewGameRequest(BaseModel):
    player_name: str
    starter_pokemon_id: int


class SaveGameRequest(BaseModel):
    player: dict


@router.post("/new")
def new_game(req: NewGameRequest):
    try:
        return create_game(req.player_name, req.starter_pokemon_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{game_id}")
def game_state(game_id: str):
    state = get_game(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return state


@router.post("/{game_id}/save")
def save(game_id: str, req: SaveGameRequest):
    state = save_game(game_id, req.player)
    if state is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return state
