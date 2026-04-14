from fastapi import APIRouter, HTTPException

from ..models.cave import (
    CaveTransitionRequest,
    CaveTransitionResponse,
    FlashRequest,
    FlashResponse,
)
from ..services.cave_service import (
    get_cave_maps,
    get_cave_state,
    get_cave_transition,
    use_flash_in_cave,
)
from ..services.game_service import get_game

router = APIRouter(prefix="/api/cave", tags=["cave"])


@router.get("/state/{game_id}/{map_id}")
def cave_state(game_id: str, map_id: str):
    """Get cave darkness state."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    state = get_cave_state(game_id, map_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Not a cave map")

    return state.model_dump()


@router.post("/flash", response_model=FlashResponse)
def use_flash(req: FlashRequest):
    """Use Flash to light cave."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return use_flash_in_cave(req.game_id, req.map_id, req.pokemon_index)


@router.post("/transition", response_model=CaveTransitionResponse)
def cave_transition(req: CaveTransitionRequest):
    """Move between cave floors."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    result = get_cave_transition(req.game_id, req.from_map_id, req.ladder_x, req.ladder_y)
    if result is None:
        raise HTTPException(status_code=404, detail="No transition at this location")

    return result


@router.get("/maps")
def list_cave_maps():
    """List all cave maps."""
    return get_cave_maps()
