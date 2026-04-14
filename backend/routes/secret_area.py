from fastapi import APIRouter, HTTPException

from ..models.secret_area import DiscoverAreaRequest, DiscoverAreaResponse, SecretAreaProgress
from ..services.secret_area_service import (
    check_tile_for_secret,
    discover_area,
    get_discovered_areas,
    load_secret_areas,
)
from ..services.game_service import get_game

router = APIRouter(prefix="/api/secret", tags=["secret_areas"])


@router.post("/check", response_model=DiscoverAreaResponse)
def check_secret(req: DiscoverAreaRequest):
    """Check if current tile is a secret area trigger."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    area = check_tile_for_secret(req.game_id, req.map_id, req.x, req.y)
    if area is None:
        return DiscoverAreaResponse(discovered=False)

    return DiscoverAreaResponse(
        discovered=True,
        area_id=area.id,
        display_name=area.display_name,
        message=area.discovery_message,
    )


@router.post("/discover", response_model=DiscoverAreaResponse)
def discover_secret(req: DiscoverAreaRequest):
    """Discover and unlock a secret area."""
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    # Find the area at this tile
    area = check_tile_for_secret(req.game_id, req.map_id, req.x, req.y)
    if area is None:
        return DiscoverAreaResponse(discovered=False, message="No secret area here.")

    result = discover_area(req.game_id, area.id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to discover area")
    return result


@router.get("/progress/{game_id}", response_model=SecretAreaProgress)
def get_progress(game_id: str):
    """Get all discovered areas for a game."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    discovered = get_discovered_areas(game_id)
    return SecretAreaProgress(game_id=game_id, discovered_areas=discovered)


@router.get("/areas")
def list_areas():
    """List all secret area metadata (for debug/admin)."""
    areas = load_secret_areas()
    return [a.model_dump() for a in areas]
