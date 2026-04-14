from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.game_service import get_game
from ..services.ss_anne_service import (
    board_ship,
    defeat_rival,
    get_state,
    help_captain,
    receive_hm,
)

router = APIRouter(prefix="/api/ss-anne", tags=["ss-anne"])


class SSAnneRequest(BaseModel):
    game_id: str


class BoardRequest(BaseModel):
    game_id: str
    has_ticket: bool


@router.get("/state/{game_id}")
def ss_anne_state(game_id: str):
    """Get S.S. Anne event state."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_state(game_id)


@router.post("/board")
def board(req: BoardRequest):
    """Board the S.S. Anne."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = board_ship(req.game_id, req.has_ticket)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot board"))
    return result


@router.post("/rival")
def rival(req: SSAnneRequest):
    """Record rival defeat on the S.S. Anne."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = defeat_rival(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot defeat rival"))
    return result


@router.post("/captain")
def captain(req: SSAnneRequest):
    """Help the seasick captain."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = help_captain(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot help captain"))
    return result


@router.post("/hm")
def hm(req: SSAnneRequest):
    """Receive HM01 Cut from the captain."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = receive_hm(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot receive HM"))
    return result
