from fastapi import APIRouter, HTTPException

from ..models.hm_overworld import (
    BoulderPushRequest,
    BoulderPushResponse,
    SurfStateRequest,
    UseHMRequest,
    UseHMResponse,
)
from ..services.hm_overworld_service import (
    exit_surf,
    get_obstacle_states,
    get_obstacles_for_map,
    get_surf_state,
    push_boulder,
    use_cut,
    use_flash,
    use_strength,
    use_surf,
)
from ..services.game_service import get_game

router = APIRouter(prefix="/api/hm", tags=["hm_overworld"])


@router.post("/use", response_model=UseHMResponse)
def use_hm(req: UseHMRequest):
    """Use an HM move in overworld (Cut, Surf, Strength, Flash)."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    handlers = {
        "Cut": lambda: use_cut(req.game_id, req.map_id, req.target_x, req.target_y, req.pokemon_index),
        "Surf": lambda: use_surf(req.game_id, req.map_id, req.target_x, req.target_y, req.pokemon_index),
        "Strength": lambda: use_strength(req.game_id, req.map_id, req.target_x, req.target_y, req.pokemon_index),
        "Flash": lambda: use_flash(req.game_id, req.map_id, req.pokemon_index),
    }

    handler = handlers.get(req.hm_move)
    if handler is None:
        return UseHMResponse(success=False, message=f"Unknown HM move: {req.hm_move}")

    return handler()


@router.post("/boulder/push", response_model=BoulderPushResponse)
def push_boulder_endpoint(req: BoulderPushRequest):
    """Push a boulder in a direction."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return push_boulder(req.game_id, req.obstacle_id, req.direction)


@router.get("/obstacles/{map_id}")
def get_obstacles(map_id: str):
    """Get all obstacles on a map."""
    obstacles = get_obstacles_for_map(map_id)
    return [o.model_dump() for o in obstacles]


@router.get("/obstacles/{map_id}/state/{game_id}")
def get_obstacles_state(map_id: str, game_id: str):
    """Get obstacle state (removed/pushed) for a game."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return get_obstacle_states(game_id, map_id)


@router.get("/surf/state/{game_id}")
def surf_state(game_id: str):
    """Check player surf state."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return {"surfing": get_surf_state(game_id)}


@router.post("/surf/exit")
def exit_surfing(req: SurfStateRequest):
    """Exit surfing state."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    success = exit_surf(req.game_id)
    return {"success": success, "message": "You got out of the water!" if success else "You're not surfing!"}
