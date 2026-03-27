from fastapi import APIRouter, HTTPException

from ..models.map import BuildingEnterRequest, MapTransitionRequest, PlayerMoveRequest
from ..services.map_service import (
    enter_building,
    exit_building,
    get_all_maps,
    get_current_map,
    get_map,
    get_map_connections,
    move_player,
    transition_map,
)

router = APIRouter(tags=["maps"])


@router.get("/api/maps")
def list_maps():
    maps = get_all_maps()
    return [{"id": m.id, "name": m.display_name, "type": m.map_type} for m in maps]


@router.get("/api/maps/current/{game_id}")
def current_map(game_id: str):
    result = get_current_map(game_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.get("/api/maps/{map_id}")
def map_detail(map_id: str):
    result = get_map(map_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Map not found")
    return result


@router.get("/api/maps/{map_id}/connections")
def map_connections(map_id: str):
    return get_map_connections(map_id)


@router.post("/api/maps/transition")
def map_transition(req: MapTransitionRequest):
    result = transition_map(req.game_id, req.from_map, req.direction)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot transition in that direction")
    return result


@router.post("/api/maps/enter-building")
def building_enter(req: BuildingEnterRequest):
    result = enter_building(req.game_id, req.building_door_x, req.building_door_y)
    if result is None:
        raise HTTPException(status_code=400, detail="No building entrance at that position")
    return result


@router.post("/api/maps/exit-building/{game_id}")
def building_exit(game_id: str):
    result = exit_building(game_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Not in a building")
    return result


@router.post("/api/player/move")
def player_move(req: PlayerMoveRequest):
    result = move_player(req.game_id, req.x, req.y, req.facing)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result
