from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.game_service import get_game
from ..services.bill_event_service import (
    complete_transformation,
    get_state,
    give_ss_ticket,
    start_transformation,
)

router = APIRouter(prefix="/api/bill", tags=["bill-event"])


class BillRequest(BaseModel):
    game_id: str


@router.get("/state/{game_id}")
def bill_state(game_id: str):
    """Get Bill's current event state."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_state(game_id)


@router.post("/transform")
def transform(req: BillRequest):
    """Start the transformation event."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = start_transformation(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot transform"))
    return result


@router.post("/complete")
def complete(req: BillRequest):
    """Complete the transformation."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = complete_transformation(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot complete"))
    return result


@router.post("/ticket")
def ticket(req: BillRequest):
    """Receive S.S. Ticket from Bill."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = give_ss_ticket(req.game_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot give ticket"))
    return result
