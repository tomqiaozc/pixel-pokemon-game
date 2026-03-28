"""Pokemon breeding and daycare API routes."""
from fastapi import APIRouter, HTTPException

from ..models.breeding import (
    CollectEggRequest,
    DepositRequest,
    StepRequest,
    WithdrawRequest,
)
from ..services.breeding_service import (
    collect_egg,
    deposit_pokemon,
    get_daycare_status,
    process_steps,
    withdraw_pokemon,
)
from ..services.game_service import get_game

router = APIRouter(prefix="/api/daycare", tags=["daycare"])


@router.get("/status/{game_id}")
def daycare_status(game_id: str):
    """Check daycare state, egg availability."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_daycare_status(game_id)


@router.post("/deposit")
def deposit(req: DepositRequest):
    """Deposit a Pokemon from player's team (max 2)."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        return deposit_pokemon(req.game_id, req.pokemon_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/withdraw/{slot}")
def withdraw(slot: int, req: WithdrawRequest):
    """Withdraw a Pokemon from the daycare."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        return withdraw_pokemon(req.game_id, slot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/collect-egg")
def collect(req: CollectEggRequest):
    """Pick up an egg if one is available."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        egg = collect_egg(req.game_id)
        return {"success": True, "egg": egg, "message": "You received an egg!"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/step")
def step(req: StepRequest):
    """Increment step counter — daycare EXP, egg generation, egg hatching."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    result = process_steps(req.game_id, req.steps)
    return result
