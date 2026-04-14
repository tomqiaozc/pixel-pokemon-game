from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.game_service import get_game
from ..services.trash_can_puzzle_service import (
    check_can,
    get_state,
    reset_puzzle,
)

router = APIRouter(prefix="/api/trash-puzzle", tags=["trash-puzzle"])


class PuzzleRequest(BaseModel):
    game_id: str


class CheckCanRequest(BaseModel):
    game_id: str
    can_index: int


@router.get("/state/{game_id}")
def puzzle_state(game_id: str):
    """Get trash can puzzle state."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_state(game_id)


@router.post("/check")
def check(req: CheckCanRequest):
    """Check a trash can for a switch."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return check_can(req.game_id, req.can_index)


@router.post("/reset")
def reset(req: PuzzleRequest):
    """Reset the puzzle."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return reset_puzzle(req.game_id)
