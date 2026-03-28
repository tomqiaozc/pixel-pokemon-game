"""Berry farming API routes."""
from fastapi import APIRouter, HTTPException

from ..models.berry import HarvestRequest, PlantRequest, WaterRequest
from ..services.berry_service import (
    add_berry_to_pouch,
    get_berry_defs,
    get_berry_pouch,
    get_plots,
    get_plots_for_map,
    harvest_plot,
    plant_berry,
    water_plot,
)
from ..services.game_service import get_game
from ..services.leaderboard_service import check_achievements, record_berry_harvested

router = APIRouter(prefix="/api/berry", tags=["berry"])


@router.get("/types")
def list_berry_types():
    """List all berry definitions."""
    return get_berry_defs()


@router.get("/plots/{game_id}")
def list_plots(game_id: str):
    """Get all berry plot states for a game."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_plots(game_id)


@router.get("/plots/{game_id}/{map_id}")
def list_plots_for_map(game_id: str, map_id: str):
    """Get berry plots for a specific map."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_plots_for_map(game_id, map_id)


@router.post("/plant")
def plant(req: PlantRequest):
    """Plant a berry in an empty plot."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        result = plant_berry(req.game_id, req.plot_id, req.berry_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/water/{plot_id}")
def water(plot_id: str, req: WaterRequest):
    """Water a planted berry."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        result = water_plot(req.game_id, plot_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/harvest/{plot_id}")
def harvest(plot_id: str, req: HarvestRequest):
    """Harvest a ready berry."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        result = harvest_plot(req.game_id, plot_id)
        if result.success and result.quantity > 0:
            record_berry_harvested(req.game_id, result.quantity)
            check_achievements(req.game_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inventory/{game_id}")
def berry_inventory(game_id: str):
    """Get berry pouch contents."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return get_berry_pouch(game_id)


@router.post("/give")
def give_berry(game_id: str, berry_id: str, quantity: int = 1):
    """Add berries to player's pouch (admin/gift/reward)."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        add_berry_to_pouch(game_id, berry_id, quantity)
        return {"success": True, "message": f"Added {quantity} {berry_id} berry(s)"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
