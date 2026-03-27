from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models.map import GameMap, MapTransitionResponse, PlayerMoveResponse
from .game_service import get_game

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# In-memory map storage
_maps: dict[str, GameMap] = {}


def _load_maps() -> None:
    global _maps
    with open(DATA_DIR / "maps.json") as f:
        raw = json.load(f)
    _maps = {m["id"]: GameMap(**m) for m in raw}


def _ensure_maps() -> None:
    if not _maps:
        _load_maps()


def get_map(map_id: str) -> Optional[GameMap]:
    _ensure_maps()
    return _maps.get(map_id)


def get_all_maps() -> list[GameMap]:
    _ensure_maps()
    return list(_maps.values())


def get_map_connections(map_id: str) -> list[dict]:
    _ensure_maps()
    game_map = _maps.get(map_id)
    if game_map is None:
        return []
    return [conn.model_dump() for conn in game_map.connections]


def get_current_map(game_id: str) -> Optional[GameMap]:
    game = get_game(game_id)
    if game is None:
        return None
    map_id = game["player"]["position"]["map_id"]
    return get_map(map_id)


def transition_map(game_id: str, from_map_id: str, direction: str) -> Optional[MapTransitionResponse]:
    _ensure_maps()
    source = _maps.get(from_map_id)
    if source is None:
        return None

    # Find the connection in the given direction
    for conn in source.connections:
        if conn.direction == direction:
            target = _maps.get(conn.target_map_id)
            if target is None:
                return None

            # Update player position in game state
            game = get_game(game_id)
            if game is not None:
                game["player"]["position"]["map_id"] = conn.target_map_id
                game["player"]["position"]["x"] = conn.entry_x
                game["player"]["position"]["y"] = conn.entry_y

            return MapTransitionResponse(
                target_map_id=conn.target_map_id,
                spawn_x=conn.entry_x,
                spawn_y=conn.entry_y,
                map_data=target,
            )

    return None


def enter_building(game_id: str, door_x: int, door_y: int) -> Optional[MapTransitionResponse]:
    """Transition player into a building interior when they step on its door tile."""
    game = get_game(game_id)
    if game is None:
        return None

    current_map_id = game["player"]["position"]["map_id"]
    current_map = get_map(current_map_id)
    if current_map is None:
        return None

    # Find building with matching door position
    for building in current_map.buildings:
        if building.door_x == door_x and building.door_y == door_y and building.interior_map_id:
            interior = get_map(building.interior_map_id)
            if interior is None:
                return None

            # Place player at bottom-center of interior
            spawn_x = interior.width // 2
            spawn_y = interior.height - 2

            game["player"]["position"]["map_id"] = building.interior_map_id
            game["player"]["position"]["x"] = spawn_x
            game["player"]["position"]["y"] = spawn_y

            return MapTransitionResponse(
                target_map_id=building.interior_map_id,
                spawn_x=spawn_x,
                spawn_y=spawn_y,
                map_data=interior,
            )

    return None


def exit_building(game_id: str) -> Optional[MapTransitionResponse]:
    """Exit from an interior map back to the parent map."""
    _ensure_maps()
    game = get_game(game_id)
    if game is None:
        return None

    current_map_id = game["player"]["position"]["map_id"]

    # Find which outdoor map has a building pointing to this interior
    for game_map in _maps.values():
        for building in game_map.buildings:
            if building.interior_map_id == current_map_id:
                # Place player just below the building door
                spawn_x = building.door_x
                spawn_y = building.door_y + 1

                game["player"]["position"]["map_id"] = game_map.id
                game["player"]["position"]["x"] = spawn_x
                game["player"]["position"]["y"] = spawn_y

                return MapTransitionResponse(
                    target_map_id=game_map.id,
                    spawn_x=spawn_x,
                    spawn_y=spawn_y,
                    map_data=game_map,
                )

    return None


def move_player(game_id: str, x: int, y: int, facing: str = "down") -> Optional[PlayerMoveResponse]:
    game = get_game(game_id)
    if game is None:
        return None

    current_map_id = game["player"]["position"]["map_id"]
    current_map = get_map(current_map_id)
    if current_map is None:
        return None

    # Clamp to map bounds
    x = max(0, min(x, current_map.width - 1))
    y = max(0, min(y, current_map.height - 1))

    # Update position
    game["player"]["position"]["x"] = x
    game["player"]["position"]["y"] = y
    game["player"]["position"]["facing"] = facing

    # Check if player is in an encounter zone
    in_zone = False
    zone_table_id = None
    for zone in current_map.encounter_zones:
        if zone.x <= x < zone.x + zone.width and zone.y <= y < zone.y + zone.height:
            in_zone = True
            zone_table_id = zone.encounter_table_id
            break

    return PlayerMoveResponse(
        x=x,
        y=y,
        map_id=current_map_id,
        in_encounter_zone=in_zone,
        encounter_table_id=zone_table_id,
    )
