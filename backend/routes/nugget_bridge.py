from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.game_service import get_game
from ..services.nugget_bridge_service import (
    award_nugget,
    defeat_rocket,
    defeat_trainer,
    get_state,
)

router = APIRouter(prefix="/api/nugget-bridge", tags=["nugget-bridge"])


class DefeatTrainerRequest(BaseModel):
    game_id: str
    trainer_index: int


class BridgeRequest(BaseModel):
    game_id: str


@router.get("/state/{game_id}")
def bridge_state(game_id: str):
    """Get Nugget Bridge progress."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_state(game_id)


@router.post("/defeat")
def record_defeat(req: DefeatTrainerRequest):
    """Record a trainer defeat on the bridge."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return defeat_trainer(req.game_id, req.trainer_index)


@router.post("/award")
def award(req: BridgeRequest):
    """Award Nugget after clearing all 5 trainers."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = award_nugget(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot award"))
    return result


@router.post("/rocket")
def rocket(req: BridgeRequest):
    """Record Rocket Grunt defeat."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return defeat_rocket(req.game_id)
